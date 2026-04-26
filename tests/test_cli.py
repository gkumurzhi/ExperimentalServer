"""Tests for CLI argument parsing and main() wiring."""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

import src.cli as cli
from src.cli import create_parser


def _find_free_port() -> int:
    """Reserve an ephemeral local port and return it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(port: int, timeout: float = 5.0) -> None:
    """Poll the live server until it answers a minimal PING request."""
    deadline = time.time() + timeout
    request = (
        f"PING / HTTP/1.1\r\n"
        f"Host: 127.0.0.1:{port}\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode("ascii")
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2) as sock:
                sock.settimeout(0.5)
                sock.sendall(request)
                if b"200 OK" in sock.recv(4096):
                    return
        except OSError:
            time.sleep(0.05)
    raise AssertionError("CLI server did not start in time")


class TestCLIParser:
    """Test CLI argument parsing without starting the server."""

    def setup_method(self):
        self.parser = create_parser()

    def test_defaults(self):
        args = self.parser.parse_args([])
        assert args.host == "127.0.0.1"
        assert args.port == 8080
        assert args.dir == "."
        assert args.quiet is False
        assert args.debug is False
        assert args.tls is False
        assert args.auth is None
        assert args.max_size == 100
        assert args.workers == 10
        assert args.cors_origin == ""

    def test_custom_host_port(self):
        args = self.parser.parse_args(["-H", "0.0.0.0", "-p", "443"])
        assert args.host == "0.0.0.0"
        assert args.port == 443

    @pytest.mark.parametrize("flag", ["--opsec", "--sandbox", "-o", "-s"])
    def test_removed_mode_flags_are_rejected(self, flag):
        with pytest.raises(SystemExit) as exc_info:
            self.parser.parse_args([flag])
        assert exc_info.value.code == 2

    def test_short_flags(self):
        args = self.parser.parse_args(["-q"])
        assert args.quiet is True

    def test_tls_flags(self):
        args = self.parser.parse_args(["--tls"])
        assert args.tls is True

    def test_cert_key(self):
        args = self.parser.parse_args(["--cert", "/tmp/c.pem", "--key", "/tmp/k.pem"])
        assert args.cert == "/tmp/c.pem"
        assert args.key == "/tmp/k.pem"

    def test_auth_random(self):
        args = self.parser.parse_args(["--auth", "random"])
        assert args.auth == "random"

    def test_auth_user_pass(self):
        args = self.parser.parse_args(["--auth", "admin:secret"])
        assert args.auth == "admin:secret"

    def test_max_size(self):
        args = self.parser.parse_args(["-m", "500"])
        assert args.max_size == 500

    def test_workers(self):
        args = self.parser.parse_args(["-w", "20"])
        assert args.workers == 20

    def test_debug_flag(self):
        args = self.parser.parse_args(["--debug"])
        assert args.debug is True

    def test_open_flag(self):
        args = self.parser.parse_args(["--open"])
        assert args.open is True

    def test_cors_origin_flag(self):
        args = self.parser.parse_args(["--cors-origin", "https://app.example"])
        assert args.cors_origin == "https://app.example"

    def test_letsencrypt_requires_domain(self):
        """--letsencrypt without --domain should be caught by main()."""
        # Parser itself accepts it; validation is in main()
        args = self.parser.parse_args(["--letsencrypt"])
        assert args.letsencrypt is True
        assert args.domain is None

    def test_letsencrypt_with_domain(self):
        args = self.parser.parse_args(["--letsencrypt", "--domain", "example.com"])
        assert args.letsencrypt is True
        assert args.domain == "example.com"

    def test_version_flag(self):
        with pytest.raises(SystemExit) as exc_info:
            self.parser.parse_args(["--version"])
        assert exc_info.value.code == 0

    def test_dir_flag(self):
        args = self.parser.parse_args(["-d", "/tmp/serve"])
        assert args.dir == "/tmp/serve"

    def test_json_log_flag(self):
        args = self.parser.parse_args(["--json-log"])
        assert args.json_log is True

    def test_json_log_default_false(self):
        args = self.parser.parse_args([])
        assert args.json_log is False


class TestCLIMain:
    def test_main_starts_server_with_expected_config(self, monkeypatch):
        captured: dict[str, object] = {}

        class ServerStub:
            def __init__(self, **kwargs):
                captured.update(kwargs)

            def start(self):
                captured["started"] = True

        monkeypatch.setattr(cli, "ExperimentalHTTPServer", ServerStub)

        result = cli.main(
            [
                "-H",
                "0.0.0.0",
                "-p",
                "9090",
                "-d",
                "/srv/data",
                "--quiet",
                "--debug",
                "--open",
                "--json-log",
                "--cors-origin",
                "https://app.example",
                "-m",
                "250",
                "-w",
                "20",
                "--auth",
                "admin:secret",
            ]
        )

        assert result == 0
        assert captured == {
            "host": "0.0.0.0",
            "port": 9090,
            "root_dir": "/srv/data",
            "max_upload_size": 250 * 1024 * 1024,
            "max_workers": 20,
            "quiet": True,
            "debug": True,
            "tls": False,
            "cert_file": None,
            "key_file": None,
            "letsencrypt": False,
            "domain": None,
            "email": None,
            "auth": "admin:secret",
            "open_browser": True,
            "json_log": True,
            "cors_origin": "https://app.example",
            "started": True,
        }

    @pytest.mark.parametrize(
        ("argv", "expected_tls"),
        [
            (["--tls"], True),
            (["--cert", "/tmp/cert.pem"], True),
            (["--letsencrypt", "--domain", "example.com"], True),
        ],
    )
    def test_main_enables_tls_when_any_tls_input_is_present(
        self,
        monkeypatch,
        argv,
        expected_tls,
    ):
        captured: dict[str, object] = {}

        class ServerStub:
            def __init__(self, **kwargs):
                captured.update(kwargs)

            def start(self):
                return None

        monkeypatch.setattr(cli, "ExperimentalHTTPServer", ServerStub)

        result = cli.main(argv)

        assert result == 0
        assert captured["tls"] is expected_tls

    def test_main_requires_domain_for_letsencrypt(self):
        with pytest.raises(SystemExit) as exc_info:
            cli.main(["--letsencrypt"])
        assert exc_info.value.code == 2

    def test_main_returns_zero_on_keyboard_interrupt(self, monkeypatch):
        class ServerStub:
            def __init__(self, **_kwargs):
                pass

            def start(self):
                raise KeyboardInterrupt

        monkeypatch.setattr(cli, "ExperimentalHTTPServer", ServerStub)

        assert cli.main([]) == 0

    def test_main_returns_one_and_prints_error_on_exception(self, monkeypatch, capsys):
        class ServerStub:
            def __init__(self, **_kwargs):
                raise RuntimeError("boom")

        monkeypatch.setattr(cli, "ExperimentalHTTPServer", ServerStub)

        result = cli.main([])
        captured = capsys.readouterr()

        assert result == 1
        assert "Error: boom" in captured.err

    @pytest.mark.skipif(not hasattr(signal, "SIGTERM"), reason="SIGTERM not available")
    def test_cli_process_handles_sigterm_gracefully(self, temp_dir: Path):
        port = _find_free_port()
        (temp_dir / "index.html").write_text("<html>ok</html>", encoding="utf-8")
        repo_root = Path(__file__).resolve().parents[1]
        env = {**os.environ, "PYTHONUNBUFFERED": "1"}
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "src.cli",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--dir",
                str(temp_dir),
                "--quiet",
            ],
            cwd=repo_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        try:
            _wait_for_server(port)
            process.send_signal(signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=5.0)
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5.0)

        assert process.returncode == 0
        assert "Server stopped" in stdout
        assert stderr == ""

        with pytest.raises(OSError):
            socket.create_connection(("127.0.0.1", port), timeout=0.2)

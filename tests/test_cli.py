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
from exphttp import ExperimentalHTTPServer
from src.cli import create_parser


def _find_free_port() -> int:
    """Reserve an ephemeral local port and return it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(port: int, timeout: float = 5.0) -> None:
    """Poll the live server until it answers a minimal PING request."""
    deadline = time.time() + timeout
    request = (f"PING / HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nConnection: close\r\n\r\n").encode(
        "ascii"
    )
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
        assert args.auth_file is None
        assert args.max_size == 100
        assert args.upload_storage_limit == 0
        assert args.upload_file_limit == 0
        assert args.upload_reserve_free == 0
        assert args.note_storage_limit == 256
        assert args.note_count_limit == 1000
        assert args.smuggle_temp_age == 3600
        assert args.smuggle_temp_file_limit == 32
        assert args.smuggle_temp_storage_limit == 128
        assert args.max_header_size == 64
        assert args.body_memory_budget is None
        assert args.body_idle_timeout == 5.0
        assert args.body_timeout == 300.0
        assert args.body_min_rate == 0.0
        assert args.stream_send_idle_timeout == 5.0
        assert args.stream_send_timeout == 300.0
        assert args.workers == 10
        assert args.cors_origin == ""
        assert args.advanced_upload is False
        assert args.profile == "lab"
        assert args.sslip is False
        assert args.public_ip is None
        assert args.acme_staging is False
        assert args.acme_server is None
        assert args.acme_http_address == ""
        assert args.acme_http_port == 80

    def test_custom_host_port(self):
        args = self.parser.parse_args(["-H", "0.0.0.0", "-p", "443"])
        assert args.host == "0.0.0.0"
        assert args.port == 443

    @pytest.mark.parametrize(
        "argv",
        [
            ["--port", "0"],
            ["--port", "-1"],
            ["--port", "65536"],
            ["--max-size", "0"],
            ["--max-size", "-1"],
            ["--upload-storage-limit", "-1"],
            ["--upload-file-limit", "-1"],
            ["--upload-reserve-free", "-1"],
            ["--note-storage-limit", "-1"],
            ["--note-count-limit", "-1"],
            ["--smuggle-temp-age", "-1"],
            ["--smuggle-temp-file-limit", "-1"],
            ["--smuggle-temp-storage-limit", "-1"],
            ["--max-header-size", "0"],
            ["--max-header-size", "-1"],
            ["--body-memory-budget", "0"],
            ["--body-memory-budget", "-1"],
            ["--body-idle-timeout", "-1"],
            ["--body-timeout", "-1"],
            ["--body-min-rate", "-1"],
            ["--stream-send-idle-timeout", "0"],
            ["--stream-send-idle-timeout", "-1"],
            ["--stream-send-timeout", "-1"],
            ["--workers", "0"],
            ["--workers", "-1"],
            ["--acme-http-port", "0"],
            ["--acme-http-port", "65536"],
        ],
    )
    def test_numeric_limits_are_rejected_at_parse_time(self, argv):
        with pytest.raises(SystemExit) as exc_info:
            self.parser.parse_args(argv)
        assert exc_info.value.code == 2

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

    def test_auth_file(self):
        args = self.parser.parse_args(["--auth-file", "/run/secrets/exphttp_auth"])
        assert args.auth_file == "/run/secrets/exphttp_auth"

    def test_max_size(self):
        args = self.parser.parse_args(["-m", "500"])
        assert args.max_size == 500

    def test_workers(self):
        args = self.parser.parse_args(["-w", "20"])
        assert args.workers == 20

    def test_body_memory_budget(self):
        args = self.parser.parse_args(["--body-memory-budget", "512"])
        assert args.body_memory_budget == 512

    def test_body_and_stream_timeout_flags(self):
        args = self.parser.parse_args(
            [
                "--body-idle-timeout",
                "1.5",
                "--body-timeout",
                "20",
                "--body-min-rate",
                "128",
                "--stream-send-idle-timeout",
                "2.5",
                "--stream-send-timeout",
                "30",
            ]
        )
        assert args.body_idle_timeout == 1.5
        assert args.body_timeout == 20.0
        assert args.body_min_rate == 128.0
        assert args.stream_send_idle_timeout == 2.5
        assert args.stream_send_timeout == 30.0

    def test_debug_flag(self):
        args = self.parser.parse_args(["--debug"])
        assert args.debug is True

    def test_open_flag(self):
        args = self.parser.parse_args(["--open"])
        assert args.open is True

    def test_cors_origin_flag(self):
        args = self.parser.parse_args(["--cors-origin", "https://app.example"])
        assert args.cors_origin == "https://app.example"

    def test_advanced_upload_flag_is_accepted_for_compatibility(self):
        args = self.parser.parse_args(["--advanced-upload"])
        assert args.advanced_upload is True

    def test_profile_flag_selects_capability_profile(self):
        args = self.parser.parse_args(["--profile", "workspace"])
        assert args.profile == "workspace"

    def test_invalid_profile_is_rejected(self):
        with pytest.raises(SystemExit) as exc_info:
            self.parser.parse_args(["--profile", "unsafe"])
        assert exc_info.value.code == 2

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

    def test_sslip_flags(self):
        args = self.parser.parse_args(["--sslip", "--public-ip", "8.8.8.8"])
        assert args.sslip is True
        assert args.public_ip == "8.8.8.8"

    def test_acme_flags(self):
        args = self.parser.parse_args(
            [
                "--acme-staging",
                "--acme-server",
                "https://acme.example/directory",
                "--acme-http-address",
                "127.0.0.1",
                "--acme-http-port",
                "5002",
            ]
        )
        assert args.acme_staging is True
        assert args.acme_server == "https://acme.example/directory"
        assert args.acme_http_address == "127.0.0.1"
        assert args.acme_http_port == 5002

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
    def test_advanced_upload_alias_conflicts_with_safe_profiles(self):
        with pytest.raises(SystemExit) as exc_info:
            cli.main(["--advanced-upload", "--profile", "serve"])
        assert exc_info.value.code == 2

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
                "--advanced-upload",
                "-m",
                "250",
                "--upload-storage-limit",
                "1000",
                "--upload-file-limit",
                "25",
                "--upload-reserve-free",
                "500",
                "--note-storage-limit",
                "128",
                "--note-count-limit",
                "50",
                "--smuggle-temp-age",
                "120",
                "--smuggle-temp-file-limit",
                "5",
                "--smuggle-temp-storage-limit",
                "32",
                "--max-header-size",
                "128",
                "--body-memory-budget",
                "512",
                "--body-idle-timeout",
                "1.5",
                "--body-timeout",
                "20",
                "--body-min-rate",
                "128",
                "--stream-send-idle-timeout",
                "2.5",
                "--stream-send-timeout",
                "30",
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
            "upload_storage_limit": 1000 * 1024 * 1024,
            "upload_file_limit": 25,
            "upload_reserved_free_space": 500 * 1024 * 1024,
            "note_storage_limit": 128 * 1024 * 1024,
            "note_count_limit": 50,
            "smuggle_temp_max_age": 120,
            "smuggle_temp_file_limit": 5,
            "smuggle_temp_storage_limit": 32 * 1024 * 1024,
            "max_header_size": 128 * 1024,
            "body_memory_budget": 512 * 1024 * 1024,
            "body_idle_timeout": 1.5,
            "body_timeout": 20.0,
            "body_min_rate": 128.0,
            "stream_send_idle_timeout": 2.5,
            "stream_send_timeout": 30.0,
            "max_workers": 20,
            "quiet": True,
            "debug": True,
            "tls": False,
            "cert_file": None,
            "key_file": None,
            "letsencrypt": False,
            "domain": None,
            "email": None,
            "sslip": False,
            "public_ip": None,
            "acme_staging": False,
            "acme_server": None,
            "acme_http_address": "",
            "acme_http_port": 80,
            "auth": "admin:secret",
            "auth_file": None,
            "open_browser": True,
            "json_log": True,
            "cors_origin": "https://app.example",
            "profile": "lab",
            "started": True,
        }

    def test_main_passes_auth_file_to_server(self, monkeypatch):
        captured: dict[str, object] = {}

        class ServerStub:
            def __init__(self, **kwargs):
                captured.update(kwargs)

            def start(self):
                captured["started"] = True

        monkeypatch.setattr(cli, "ExperimentalHTTPServer", ServerStub)

        result = cli.main(["--auth-file", "/run/secrets/exphttp_auth"])

        assert result == 0
        assert captured["auth"] is None
        assert captured["auth_file"] == "/run/secrets/exphttp_auth"

    @pytest.mark.parametrize(
        ("argv", "expected_tls"),
        [
            (["--tls"], True),
            (["--cert", "/tmp/cert.pem", "--key", "/tmp/key.pem"], True),
            (["--letsencrypt", "--domain", "example.com"], True),
            (["--sslip"], True),
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

    @pytest.mark.parametrize(
        ("argv", "message"),
        [
            (["--cert", "cert.pem"], "--cert and --key must be provided together"),
            (["--key", "key.pem"], "--cert and --key must be provided together"),
            (["--cert", ""], "--cert and --key must be provided together"),
            (["--key", ""], "--cert and --key must be provided together"),
            (["--cert", "", "--key", ""], "--cert and --key values must not be empty"),
            (
                [
                    "--cert",
                    "cert.pem",
                    "--key",
                    "key.pem",
                    "--letsencrypt",
                    "--domain",
                    "example.com",
                ],
                "--cert/--key cannot be combined with --letsencrypt or --sslip",
            ),
            (
                ["--cert", "cert.pem", "--key", "key.pem", "--sslip"],
                "--cert/--key cannot be combined with --letsencrypt or --sslip",
            ),
        ],
    )
    def test_main_rejects_invalid_tls_source_combinations(
        self,
        monkeypatch,
        capsys,
        argv,
        message,
    ):
        def fail_if_called(**_kwargs):
            raise AssertionError("server should not be constructed for invalid CLI config")

        monkeypatch.setattr(cli, "ExperimentalHTTPServer", fail_if_called)

        with pytest.raises(SystemExit) as exc_info:
            cli.main(argv)

        assert exc_info.value.code == 2
        assert message in capsys.readouterr().err

    def test_main_allows_letsencrypt_with_sslip_without_domain(self, monkeypatch):
        captured: dict[str, object] = {}

        class ServerStub:
            def __init__(self, **kwargs):
                captured.update(kwargs)

            def start(self):
                return None

        monkeypatch.setattr(cli, "ExperimentalHTTPServer", ServerStub)

        result = cli.main(["--letsencrypt", "--sslip"])

        assert result == 0
        assert captured["tls"] is True
        assert captured["letsencrypt"] is True
        assert captured["sslip"] is True

    @pytest.mark.parametrize(
        "argv",
        [
            ["--sslip", "--domain", "example.com"],
            ["--public-ip", "8.8.8.8"],
            ["--acme-http-port", "0"],
            ["--acme-http-port", "70000"],
            ["--auth-file", ""],
        ],
    )
    def test_main_rejects_invalid_acme_combinations(self, argv):
        with pytest.raises(SystemExit) as exc_info:
            cli.main(argv)
        assert exc_info.value.code == 2

    def test_main_rejects_conflicting_auth_sources_without_echoing_secret(
        self,
        monkeypatch,
        capsys,
    ):
        def fail_if_called(**_kwargs):
            raise AssertionError("server should not be constructed for invalid CLI config")

        monkeypatch.setattr(cli, "ExperimentalHTTPServer", fail_if_called)

        with pytest.raises(SystemExit) as exc_info:
            cli.main(["--auth", "admin:supersecret", "--auth-file", "/run/secrets/auth"])

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "--auth and --auth-file cannot be combined" in captured.err
        assert "supersecret" not in captured.err

    def test_main_auth_file_parse_failure_does_not_echo_secret(self, temp_dir: Path, capsys):
        auth_file = temp_dir / "auth.txt"
        auth_file.write_text("admin:supersecret\nother:credential\n", encoding="utf-8")

        result = cli.main(["-d", str(temp_dir), "--auth-file", str(auth_file)])
        captured = capsys.readouterr()

        assert result == 1
        assert "auth file must contain exactly one user:password line" in captured.err
        assert "supersecret" not in captured.err

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
                "exphttp",
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


class TestServerConstructorValidation:
    def test_zero_upload_storage_limits_disable_policy(self, temp_dir: Path):
        server = ExperimentalHTTPServer(
            root_dir=str(temp_dir),
            quiet=True,
            upload_storage_limit=0,
            upload_file_limit=0,
            upload_reserved_free_space=0,
            note_storage_limit=0,
            note_count_limit=0,
            smuggle_temp_max_age=0,
            smuggle_temp_file_limit=0,
            smuggle_temp_storage_limit=0,
        )

        assert server.upload_storage_policy.max_total_bytes is None
        assert server.upload_storage_policy.max_file_count is None
        assert server.upload_storage_policy.reserved_free_bytes == 0
        assert server.note_storage_policy.max_total_bytes is None
        assert server.note_storage_policy.max_note_count is None
        assert server.note_storage_policy.max_listed_notes == 1000
        assert server.smuggle_temp_policy.max_age_seconds is None
        assert server.smuggle_temp_policy.max_file_count is None
        assert server.smuggle_temp_policy.max_total_bytes is None

    @pytest.mark.parametrize(
        ("kwargs", "message"),
        [
            ({"port": 0}, "port must be between 1 and 65535"),
            ({"port": -1}, "port must be between 1 and 65535"),
            ({"port": 65536}, "port must be between 1 and 65535"),
            ({"max_upload_size": 0}, "max_upload_size must be greater than 0"),
            ({"max_upload_size": -1}, "max_upload_size must be greater than 0"),
            ({"upload_storage_limit": -1}, "upload_storage_limit must be at least 0"),
            ({"upload_file_limit": -1}, "upload_file_limit must be at least 0"),
            (
                {"upload_reserved_free_space": -1},
                "upload_reserved_free_space must be at least 0",
            ),
            ({"note_storage_limit": -1}, "note_storage_limit must be at least 0"),
            ({"note_count_limit": -1}, "note_count_limit must be at least 0"),
            ({"smuggle_temp_max_age": -1}, "smuggle_temp_max_age must be at least 0"),
            (
                {"smuggle_temp_file_limit": -1},
                "smuggle_temp_file_limit must be at least 0",
            ),
            (
                {"smuggle_temp_storage_limit": -1},
                "smuggle_temp_storage_limit must be at least 0",
            ),
            ({"max_header_size": 0}, "max_header_size must be greater than 0"),
            ({"max_header_size": -1}, "max_header_size must be greater than 0"),
            ({"body_memory_budget": 0}, "body_memory_budget must be greater than 0"),
            ({"body_memory_budget": -1}, "body_memory_budget must be greater than 0"),
            ({"body_idle_timeout": 0}, "body_idle_timeout must be greater than 0"),
            ({"body_idle_timeout": -1}, "body_idle_timeout must be greater than 0"),
            ({"body_timeout": 0}, "body_timeout must be greater than 0"),
            ({"body_timeout": -1}, "body_timeout must be greater than 0"),
            ({"body_min_rate": -1}, "body_min_rate must be at least 0"),
            (
                {"stream_send_idle_timeout": 0},
                "stream_send_idle_timeout must be greater than 0",
            ),
            (
                {"stream_send_idle_timeout": -1},
                "stream_send_idle_timeout must be greater than 0",
            ),
            ({"stream_send_timeout": 0}, "stream_send_timeout must be greater than 0"),
            ({"stream_send_timeout": -1}, "stream_send_timeout must be greater than 0"),
            ({"max_workers": 0}, "max_workers must be greater than 0"),
            ({"max_workers": -1}, "max_workers must be greater than 0"),
        ],
    )
    def test_invalid_primary_limits_fail_before_filesystem_side_effects(
        self,
        temp_dir: Path,
        kwargs,
        message,
    ):
        with pytest.raises(ValueError, match=message):
            ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, **kwargs)

        assert not (temp_dir / "uploads").exists()
        assert not (temp_dir / "notes").exists()

"""Tests for CLI argument parsing (B44)."""

import pytest

from src.cli import create_parser


class TestCLIParser:
    """Test CLI argument parsing without starting the server."""

    def setup_method(self):
        self.parser = create_parser()

    def test_defaults(self):
        args = self.parser.parse_args([])
        assert args.host == "127.0.0.1"
        assert args.port == 8080
        assert args.dir == "."
        assert args.opsec is False
        assert args.sandbox is False
        assert args.quiet is False
        assert args.debug is False
        assert args.tls is False
        assert args.auth is None
        assert args.max_size == 100
        assert args.workers == 10

    def test_custom_host_port(self):
        args = self.parser.parse_args(["-H", "0.0.0.0", "-p", "443"])
        assert args.host == "0.0.0.0"
        assert args.port == 443

    def test_opsec_sandbox(self):
        args = self.parser.parse_args(["--opsec", "--sandbox"])
        assert args.opsec is True
        assert args.sandbox is True

    def test_short_flags(self):
        args = self.parser.parse_args(["-o", "-s", "-q"])
        assert args.opsec is True
        assert args.sandbox is True
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

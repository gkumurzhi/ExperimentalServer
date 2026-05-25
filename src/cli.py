#!/usr/bin/env python3
"""
CLI entry point for ExperimentalHTTPServer.
"""

import argparse
import signal
import sys
from collections.abc import Callable, Sequence
from types import FrameType
from typing import Any

from . import ExperimentalHTTPServer, __version__
from .handlers.smuggle import (
    DEFAULT_SMUGGLE_TEMP_MAX_AGE_SECONDS,
    DEFAULT_SMUGGLE_TEMP_MAX_BYTES,
    DEFAULT_SMUGGLE_TEMP_MAX_FILES,
)
from .http.io import DEFAULT_MAX_HEADER_SIZE
from .notepad_service import DEFAULT_MAX_NOTE_STORAGE_BYTES, DEFAULT_MAX_NOTES

_MIB = 1024 * 1024


def _bounded_int(name: str, *, minimum: int, maximum: int | None = None) -> Callable[[str], int]:
    """Return an argparse type function for an integer with inclusive bounds."""

    def parse(value: str) -> int:
        try:
            parsed = int(value, 10)
        except ValueError:
            raise argparse.ArgumentTypeError(f"{name} must be an integer") from None

        if parsed < minimum:
            if maximum is None:
                raise argparse.ArgumentTypeError(f"{name} must be at least {minimum}")
            raise argparse.ArgumentTypeError(f"{name} must be between {minimum} and {maximum}")
        if maximum is not None and parsed > maximum:
            raise argparse.ArgumentTypeError(f"{name} must be between {minimum} and {maximum}")
        return parsed

    return parse


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="exphttp",
        description="HTTP server with custom methods, TLS, Auth, and uploads-only file access.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Quick start:
    exphttp                    → http://127.0.0.1:8080
    exphttp --open             → start + open browser
    exphttp --tls --auth random → HTTPS + random password

Examples:
    exphttp -H 0.0.0.0 -p 443 --tls    Public HTTPS
    exphttp -d ./data -m 500            Custom dir, 500 MB limit

Custom HTTP methods:
    FETCH, INFO, PING, NONE, SMUGGLE    (+ standard GET, POST, PUT, OPTIONS)
        """,
    )

    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")

    # Basic
    basic = parser.add_argument_group("Basic")
    basic.add_argument(
        "-H", "--host", default="127.0.0.1", metavar="HOST", help="Bind host (default: 127.0.0.1)"
    )
    basic.add_argument(
        "-p",
        "--port",
        type=_bounded_int("port", minimum=1, maximum=65535),
        default=8080,
        metavar="PORT",
        help="Listen port (default: 8080)",
    )
    basic.add_argument(
        "-d", "--dir", default=".", metavar="DIR", help="Root directory (default: current)"
    )

    # Operating modes
    modes = parser.add_argument_group("Modes")
    modes.add_argument("-q", "--quiet", action="store_true", help="Quiet mode (minimal logging)")
    modes.add_argument("--debug", action="store_true", help="Debug mode (verbose logging)")
    modes.add_argument("--open", action="store_true", help="Open browser after start")
    modes.add_argument("--json-log", action="store_true", help="Structured JSON log format")
    modes.add_argument(
        "--cors-origin",
        default="",
        metavar="ORIGIN",
        help="Enable CORS for an explicit origin (default: disabled)",
    )
    modes.add_argument(
        "--advanced-upload",
        action="store_true",
        help="Deprecated no-op; advanced upload is always enabled",
    )

    # Limits
    limits = parser.add_argument_group("Limits")
    limits.add_argument(
        "-m",
        "--max-size",
        type=_bounded_int("max size", minimum=1),
        default=100,
        metavar="MB",
        help="Max per-request upload body size in MB (default: 100)",
    )
    limits.add_argument(
        "--upload-storage-limit",
        type=_bounded_int("upload storage limit", minimum=0),
        default=0,
        metavar="MB",
        help="Aggregate uploads/ storage quota in MB; 0 disables (default: 0)",
    )
    limits.add_argument(
        "--upload-file-limit",
        type=_bounded_int("upload file limit", minimum=0),
        default=0,
        metavar="N",
        help="Aggregate uploads/ file count quota; 0 disables (default: 0)",
    )
    limits.add_argument(
        "--upload-reserve-free",
        type=_bounded_int("upload reserve free", minimum=0),
        default=0,
        metavar="MB",
        help="Minimum free disk space to preserve while committing uploads in MB (default: 0)",
    )
    limits.add_argument(
        "--note-storage-limit",
        type=_bounded_int("note storage limit", minimum=0),
        default=DEFAULT_MAX_NOTE_STORAGE_BYTES // _MIB,
        metavar="MB",
        help=(
            "Aggregate encrypted notes/ blob quota in MB; 0 disables "
            f"(default: {DEFAULT_MAX_NOTE_STORAGE_BYTES // _MIB})"
        ),
    )
    limits.add_argument(
        "--note-count-limit",
        type=_bounded_int("note count limit", minimum=0),
        default=DEFAULT_MAX_NOTES,
        metavar="N",
        help=f"Aggregate encrypted note count quota; 0 disables (default: {DEFAULT_MAX_NOTES})",
    )
    limits.add_argument(
        "--smuggle-temp-age",
        type=_bounded_int("SMUGGLE temp max age", minimum=0),
        default=DEFAULT_SMUGGLE_TEMP_MAX_AGE_SECONDS,
        metavar="SECONDS",
        help=(
            "Max age for retained SMUGGLE temp pages in seconds; 0 disables "
            f"(default: {DEFAULT_SMUGGLE_TEMP_MAX_AGE_SECONDS})"
        ),
    )
    limits.add_argument(
        "--smuggle-temp-file-limit",
        type=_bounded_int("SMUGGLE temp file limit", minimum=0),
        default=DEFAULT_SMUGGLE_TEMP_MAX_FILES,
        metavar="N",
        help=(
            "Max retained SMUGGLE temp page count; 0 disables "
            f"(default: {DEFAULT_SMUGGLE_TEMP_MAX_FILES})"
        ),
    )
    limits.add_argument(
        "--smuggle-temp-storage-limit",
        type=_bounded_int("SMUGGLE temp storage limit", minimum=0),
        default=DEFAULT_SMUGGLE_TEMP_MAX_BYTES // _MIB,
        metavar="MB",
        help=(
            "Max retained SMUGGLE temp page bytes in MB; 0 disables "
            f"(default: {DEFAULT_SMUGGLE_TEMP_MAX_BYTES // _MIB})"
        ),
    )
    limits.add_argument(
        "--max-header-size",
        type=_bounded_int("max header size", minimum=1),
        default=DEFAULT_MAX_HEADER_SIZE // 1024,
        metavar="KB",
        help="Max HTTP request header size in KiB (default: 64)",
    )
    limits.add_argument(
        "-w",
        "--workers",
        type=_bounded_int("workers", minimum=1),
        default=10,
        metavar="N",
        help="Number of worker threads (default: 10)",
    )

    # TLS options
    tls = parser.add_argument_group("TLS")
    tls.add_argument(
        "--tls", action="store_true", help="Enable HTTPS (generates self-signed certificate)"
    )
    tls.add_argument("--cert", metavar="FILE", help="Path to certificate file (PEM)")
    tls.add_argument("--key", metavar="FILE", help="Path to private key file (PEM)")
    tls.add_argument(
        "--letsencrypt",
        action="store_true",
        help="Obtain Let's Encrypt certificate with built-in ACME HTTP-01",
    )
    tls.add_argument("--domain", metavar="DOMAIN", help="Domain for Let's Encrypt certificate")
    tls.add_argument(
        "--email", metavar="EMAIL", help="Email for Let's Encrypt notifications (optional)"
    )
    tls.add_argument(
        "--sslip",
        action="store_true",
        help="Obtain a Let's Encrypt certificate for the public IPv4 sslip.io hostname",
    )
    tls.add_argument(
        "--public-ip",
        metavar="IP",
        help="Public IPv4 override for --sslip (default: auto-detect)",
    )
    tls.add_argument(
        "--acme-staging",
        action="store_true",
        help="Use Let's Encrypt staging ACME directory",
    )
    tls.add_argument(
        "--acme-server",
        metavar="URL",
        help="Custom ACME directory URL (overrides --acme-staging)",
    )
    tls.add_argument(
        "--acme-http-address",
        default="",
        metavar="ADDR",
        help="Bind address for HTTP-01 challenge server (default: all interfaces)",
    )
    tls.add_argument(
        "--acme-http-port",
        type=_bounded_int("ACME HTTP port", minimum=1, maximum=65535),
        default=80,
        metavar="PORT",
        help="Bind port for HTTP-01 challenge server (default: 80)",
    )

    # Authentication
    auth = parser.add_argument_group("Authentication")
    auth.add_argument(
        "--auth",
        metavar="CREDS",
        help="Basic Auth: 'user:pass', 'random', or 'user' (random password)",
    )

    return parser


def _validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    acme_mode = args.letsencrypt or args.sslip
    has_cert = args.cert is not None
    has_key = args.key is not None

    if has_cert != has_key:
        parser.error("--cert and --key must be provided together")
    if has_cert and (not args.cert or not args.key):
        parser.error("--cert and --key values must not be empty")
    if has_cert and acme_mode:
        parser.error("--cert/--key cannot be combined with --letsencrypt or --sslip")

    if args.letsencrypt and not args.domain and not args.sslip:
        parser.error("--letsencrypt requires --domain unless --sslip is used")
    if args.sslip and args.domain:
        parser.error("--sslip cannot be combined with --domain")
    if args.public_ip and not args.sslip:
        parser.error("--public-ip requires --sslip")

    if not acme_mode:
        acme_only_flags = [
            ("--domain", args.domain),
            ("--email", args.email),
            ("--acme-staging", args.acme_staging),
            ("--acme-server", args.acme_server),
            ("--acme-http-address", args.acme_http_address),
            ("--acme-http-port", args.acme_http_port != 80),
        ]
        for flag, active in acme_only_flags:
            if active:
                parser.error(f"{flag} requires --letsencrypt or --sslip")


def _install_shutdown_signal_handlers(server: ExperimentalHTTPServer) -> dict[signal.Signals, Any]:
    """Install graceful shutdown handlers for container-style termination."""
    previous_handlers: dict[signal.Signals, Any] = {}
    sigterm = getattr(signal, "SIGTERM", None)
    if sigterm is None:
        return previous_handlers

    def _handle_shutdown(_signum: int, _frame: FrameType | None) -> None:
        server.stop()

    previous_handlers[sigterm] = signal.getsignal(sigterm)
    signal.signal(sigterm, _handle_shutdown)
    return previous_handlers


def _restore_signal_handlers(previous_handlers: dict[signal.Signals, Any]) -> None:
    """Restore any signal handlers replaced for graceful shutdown."""
    for sig, handler in previous_handlers.items():
        signal.signal(sig, handler)


def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)
    _validate_args(parser, args)

    # Build config from arguments
    config = {
        "host": args.host,
        "port": args.port,
        "root_dir": args.dir,
        "max_upload_size": args.max_size * 1024 * 1024,
        "upload_storage_limit": (
            args.upload_storage_limit * _MIB if args.upload_storage_limit else None
        ),
        "upload_file_limit": args.upload_file_limit or None,
        "upload_reserved_free_space": args.upload_reserve_free * _MIB,
        "note_storage_limit": args.note_storage_limit * _MIB if args.note_storage_limit else None,
        "note_count_limit": args.note_count_limit or None,
        "smuggle_temp_max_age": args.smuggle_temp_age or None,
        "smuggle_temp_file_limit": args.smuggle_temp_file_limit or None,
        "smuggle_temp_storage_limit": (
            args.smuggle_temp_storage_limit * _MIB if args.smuggle_temp_storage_limit else None
        ),
        "max_header_size": args.max_header_size * 1024,
        "max_workers": args.workers,
        "quiet": args.quiet,
        "debug": args.debug,
        "tls": args.tls or bool(args.cert) or args.letsencrypt or args.sslip,
        "cert_file": args.cert,
        "key_file": args.key,
        "letsencrypt": args.letsencrypt,
        "domain": args.domain,
        "email": args.email,
        "sslip": args.sslip,
        "public_ip": args.public_ip,
        "acme_staging": args.acme_staging,
        "acme_server": args.acme_server,
        "acme_http_address": args.acme_http_address,
        "acme_http_port": args.acme_http_port,
        "auth": args.auth,
        "open_browser": args.open,
        "json_log": args.json_log,
        "cors_origin": args.cors_origin,
    }

    try:
        server = ExperimentalHTTPServer(**config)
        previous_handlers = _install_shutdown_signal_handlers(server)
        try:
            server.start()
        finally:
            _restore_signal_handlers(previous_handlers)
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

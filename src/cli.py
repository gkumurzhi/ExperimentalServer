#!/usr/bin/env python3
"""
CLI entry point for ExperimentalHTTPServer.
"""

import argparse
import sys
from collections.abc import Sequence

from . import ExperimentalHTTPServer, __version__


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="exphttp",
        description="HTTP server with custom methods, TLS, Auth, and OPSEC mode.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Quick start:
    exphttp                    → http://127.0.0.1:8080
    exphttp --open             → start + open browser
    exphttp --tls --auth random → HTTPS + random password

Examples:
    exphttp -H 0.0.0.0 -p 443 --tls    Public HTTPS
    exphttp --opsec --sandbox           OPSEC + Sandbox
    exphttp -d ./data -m 500            Custom dir, 500 MB limit

Custom HTTP methods:
    FETCH, INFO, PING, NONE, SMUGGLE    (+ standard GET, POST, PUT, OPTIONS)
        """
    )

    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    # Basic
    basic = parser.add_argument_group("Basic")
    basic.add_argument(
        "-H", "--host",
        default="127.0.0.1",
        metavar="HOST",
        help="Bind host (default: 127.0.0.1)"
    )
    basic.add_argument(
        "-p", "--port",
        type=int,
        default=8080,
        metavar="PORT",
        help="Listen port (default: 8080)"
    )
    basic.add_argument(
        "-d", "--dir",
        default=".",
        metavar="DIR",
        help="Root directory (default: current)"
    )

    # Operating modes
    modes = parser.add_argument_group("Modes")
    modes.add_argument(
        "-o", "--opsec",
        action="store_true",
        help="OPSEC mode (randomized method names, nginx masquerade)"
    )
    modes.add_argument(
        "-s", "--sandbox",
        action="store_true",
        help="Sandbox mode (restrict access to uploads/)"
    )
    modes.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet mode (minimal logging)"
    )
    modes.add_argument(
        "--debug",
        action="store_true",
        help="Debug mode (verbose logging)"
    )
    modes.add_argument(
        "--open",
        action="store_true",
        help="Open browser after start"
    )
    modes.add_argument(
        "--json-log",
        action="store_true",
        help="Structured JSON log format"
    )
    modes.add_argument(
        "--cors-origin",
        default="*",
        metavar="ORIGIN",
        help="Access-Control-Allow-Origin (default: *)"
    )

    # Limits
    limits = parser.add_argument_group("Limits")
    limits.add_argument(
        "-m", "--max-size",
        type=int,
        default=100,
        metavar="MB",
        help="Max upload size in MB (default: 100)"
    )
    limits.add_argument(
        "-w", "--workers",
        type=int,
        default=10,
        metavar="N",
        help="Number of worker threads (default: 10)"
    )

    # TLS options
    tls = parser.add_argument_group("TLS")
    tls.add_argument(
        "--tls",
        action="store_true",
        help="Enable HTTPS (generates self-signed certificate)"
    )
    tls.add_argument(
        "--cert",
        metavar="FILE",
        help="Path to certificate file (PEM)"
    )
    tls.add_argument(
        "--key",
        metavar="FILE",
        help="Path to private key file (PEM)"
    )
    tls.add_argument(
        "--letsencrypt",
        action="store_true",
        help="Obtain Let's Encrypt certificate (requires certbot and open port 80)"
    )
    tls.add_argument(
        "--domain",
        metavar="DOMAIN",
        help="Domain for Let's Encrypt certificate"
    )
    tls.add_argument(
        "--email",
        metavar="EMAIL",
        help="Email for Let's Encrypt notifications (optional)"
    )

    # Authentication
    auth = parser.add_argument_group("Authentication")
    auth.add_argument(
        "--auth",
        metavar="CREDS",
        help="Basic Auth: 'user:pass', 'random', or 'user' (random password)"
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.letsencrypt and not args.domain:
        parser.error("--letsencrypt requires --domain")

    # Build config from arguments
    config = {
        "host": args.host,
        "port": args.port,
        "root_dir": args.dir,
        "opsec_mode": args.opsec,
        "sandbox_mode": args.sandbox,
        "max_upload_size": args.max_size * 1024 * 1024,
        "max_workers": args.workers,
        "quiet": args.quiet,
        "debug": args.debug,
        "tls": args.tls or bool(args.cert) or args.letsencrypt,
        "cert_file": args.cert,
        "key_file": args.key,
        "letsencrypt": args.letsencrypt,
        "domain": args.domain,
        "email": args.email,
        "auth": args.auth,
        "open_browser": args.open,
        "json_log": args.json_log,
        "cors_origin": args.cors_origin,
    }

    try:
        server = ExperimentalHTTPServer(**config)
        server.start()
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

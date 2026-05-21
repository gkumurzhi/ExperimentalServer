"""Regression tests for package import side effects."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_probe(source: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(source)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_import_src_http_does_not_import_tls_or_acme_modules() -> None:
    result = _run_probe(
        """
        import sys

        import src.http

        imported = [
            name
            for name in sys.modules
            if name == "src.security.tls" or name.startswith(("acme", "josepy"))
        ]
        if imported:
            raise SystemExit(f"unexpected imports: {imported}")
        """
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_http_and_public_compat_imports_do_not_require_acme_modules() -> None:
    result = _run_probe(
        """
        import importlib.abc
        import sys

        class BlockAcmeAndJosepy(importlib.abc.MetaPathFinder):
            def find_spec(self, fullname, path=None, target=None):
                if fullname.startswith(("acme", "josepy")):
                    raise ImportError(f"{fullname} intentionally blocked")
                return None

        sys.meta_path.insert(0, BlockAcmeAndJosepy())

        import src.http
        import src.http.io
        import src.security
        from src import ExperimentalHTTPServer, HTTPRequest, HTTPResponse
        from src.security import BasicAuthenticator, generate_self_signed_cert

        assert HTTPRequest.__name__ == "HTTPRequest"
        assert HTTPResponse.__name__ == "HTTPResponse"
        assert ExperimentalHTTPServer.__name__ == "ExperimentalHTTPServer"
        assert BasicAuthenticator.__name__ == "BasicAuthenticator"
        assert generate_self_signed_cert.__name__ == "generate_self_signed_cert"

        imported = [name for name in sys.modules if name.startswith(("acme", "josepy"))]
        if imported:
            raise SystemExit(f"unexpected imports: {imported}")
        """
    )

    assert result.returncode == 0, result.stderr or result.stdout

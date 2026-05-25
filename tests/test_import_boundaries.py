"""Regression tests for package import side effects."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

from setuptools import find_packages

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    from setuptools._vendor import tomli as tomllib  # type: ignore[no-redef]

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


def test_public_exphttp_imports_do_not_require_acme_modules() -> None:
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

        import exphttp
        from exphttp import ExperimentalHTTPServer, HTTPRequest, HTTPResponse
        from exphttp.security import BasicAuthenticator, generate_self_signed_cert
        from exphttp.security.crypto import xor_encrypt_with_hmac

        assert exphttp.__version__
        assert HTTPRequest.__name__ == "HTTPRequest"
        assert HTTPResponse.__name__ == "HTTPResponse"
        assert ExperimentalHTTPServer.__name__ == "ExperimentalHTTPServer"
        assert BasicAuthenticator.__name__ == "BasicAuthenticator"
        assert generate_self_signed_cert.__name__ == "generate_self_signed_cert"
        assert xor_encrypt_with_hmac(b"data", "key")[1]

        imported = [name for name in sys.modules if name.startswith(("acme", "josepy"))]
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


def test_src_public_compat_imports_warn_about_exphttp_replacement() -> None:
    result = _run_probe(
        """
        import warnings

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", DeprecationWarning)
            from src import ExperimentalHTTPServer

        assert ExperimentalHTTPServer.__name__ == "ExperimentalHTTPServer"
        if not any("exphttp" in str(item.message) for item in caught):
            raise SystemExit("missing src compatibility deprecation warning")
        """
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_setuptools_package_discovery_excludes_static_asset_namespaces() -> None:
    with (REPO_ROOT / "pyproject.toml").open("rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)

    assert pyproject["tool"]["setuptools"]["include-package-data"] is False
    package_finder = pyproject["tool"]["setuptools"]["packages"]["find"]
    assert package_finder["namespaces"] is False
    assert set(package_finder["include"]) == {"exphttp*", "src*"}

    discovered_packages = set(
        find_packages(
            where=str(REPO_ROOT),
            include=package_finder["include"],
            exclude=package_finder["exclude"],
        )
    )

    assert "exphttp" in discovered_packages
    assert "src" in discovered_packages
    assert "src.data" in discovered_packages
    assert "src.data.static" not in discovered_packages
    assert "src.data.static.ui" not in discovered_packages

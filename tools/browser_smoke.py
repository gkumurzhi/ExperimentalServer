#!/usr/bin/env python3
"""Run a minimal browser smoke against a live temporary exphttp instance."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

PLAYWRIGHT_CLI_PACKAGE = "@playwright/cli@0.1.9"
SMOKE_PROFILES = ("lab", "workspace", "serve")
SMOKE_MODES = ("auto", "full", "disabled-state")


def _find_free_port() -> int:
    """Reserve an ephemeral port and return it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _path_is_under(path: Path, parent: Path) -> bool:
    """Return True when *path* is equal to or below *parent*."""
    path = path.resolve()
    parent = parent.resolve()
    return path == parent or path.is_relative_to(parent)


def _remove_repo_import_paths() -> None:
    """Remove checkout paths so installed-artifact smoke cannot import local packages."""
    filtered: list[str] = []
    for entry in sys.path:
        entry_path = Path(entry).resolve() if entry else Path.cwd().resolve()
        if _path_is_under(entry_path, REPO_ROOT):
            continue
        filtered.append(entry)
    sys.path[:] = filtered


def _load_server_class(*, installed_package: bool) -> tuple[type[Any], Path]:
    """Import ExperimentalHTTPServer from source or from the installed package."""
    if installed_package:
        _remove_repo_import_paths()
    elif str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    from exphttp import ExperimentalHTTPServer

    module = sys.modules[ExperimentalHTTPServer.__module__]
    module_path = Path(getattr(module, "__file__", "")).resolve()
    if installed_package and _path_is_under(module_path, REPO_ROOT):
        raise RuntimeError(
            "Installed-package browser smoke imported exphttp from the source checkout: "
            f"{module_path}"
        )
    return ExperimentalHTTPServer, module_path


class _LiveServer:
    """Manage a short-lived server instance for browser smoke checks."""

    def __init__(
        self,
        server_cls: type[Any],
        root_dir: Path,
        *,
        profile: str,
        disable_ecdh: bool = False,
    ) -> None:
        self.server = server_cls(
            host="127.0.0.1",
            port=_find_free_port(),
            root_dir=str(root_dir),
            quiet=True,
            profile=profile,
        )
        if disable_ecdh:
            self.server._ecdh_manager = None
        self.port = self.server.port
        self._thread = threading.Thread(target=self.server.start, daemon=True)

    def start(self) -> None:
        self._thread.start()
        for _ in range(100):
            time.sleep(0.05)
            if self.server.running:
                return
        raise RuntimeError("Server did not start in time")

    def stop(self) -> None:
        self.server.stop()
        try:
            with socket.create_connection(("127.0.0.1", self.port), timeout=0.2):
                pass
        except OSError:
            pass
        self._thread.join(timeout=3.0)


def _playwright_command() -> list[str]:
    """Return the preferred Playwright CLI invocation."""
    env_pwcli = os.environ.get("PWCLI")
    if env_pwcli:
        pwcli_path = Path(env_pwcli).expanduser()
        if pwcli_path.exists():
            return ["bash", str(pwcli_path)]

    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    bundled_pwcli = codex_home / "skills" / "playwright" / "scripts" / "playwright_cli.sh"
    if bundled_pwcli.exists():
        return ["bash", str(bundled_pwcli)]

    if shutil.which("npx"):
        return ["npx", "--yes", "--package", PLAYWRIGHT_CLI_PACKAGE, "playwright-cli"]

    raise RuntimeError("Playwright CLI not found; install Node.js/npm or set PWCLI")


def _run_playwright(
    base_cmd: list[str],
    session: str,
    *args: str,
    cwd: Path,
) -> str:
    """Run a Playwright CLI command and return stdout."""
    completed = subprocess.run(
        [*base_cmd, f"-s={session}", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "unknown playwright error"
        raise RuntimeError(message)
    outputs = [stream.strip() for stream in (completed.stdout, completed.stderr) if stream.strip()]
    return "\n".join(outputs)


def _write_cli_config(config_path: Path) -> None:
    """Write a minimal headless Playwright CLI config."""
    config = {
        "browser": {
            "launchOptions": {"headless": True},
            "contextOptions": {"viewport": {"width": 1440, "height": 1024}},
        }
    }
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")


def _parse_playwright_json(output: str) -> dict[str, object]:
    """Extract the trailing JSON object from Playwright CLI output."""
    for line in reversed([item.strip() for item in output.splitlines() if item.strip()]):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    raise RuntimeError(f"Playwright CLI did not return a JSON object. Raw output: {output!r}")


def _resolve_smoke_mode(*, profile: str, mode: str) -> str:
    """Return the concrete smoke mode for a profile."""
    if mode == "auto":
        return "full" if profile == "lab" else "disabled-state"
    if mode == "full" and profile != "lab":
        raise ValueError("--mode full requires --profile lab")
    if mode == "disabled-state" and profile == "lab":
        raise ValueError("--mode disabled-state requires --profile serve or --profile workspace")
    return mode


def run_browser_smoke(
    *,
    installed_package: bool = False,
    profile: str = "lab",
    mode: str = "auto",
) -> dict[str, object]:
    """Start temporary servers and drive the SPA through browser smoke flows."""
    smoke_mode = _resolve_smoke_mode(profile=profile, mode=mode)
    server_cls, server_module_path = _load_server_class(installed_package=installed_package)
    smoke_script = REPO_ROOT / "tools" / "browser_smoke.playwright.js"
    playwright = _playwright_command()
    session = f"exphttp-smoke-{os.getpid()}-{int(time.time())}"

    with tempfile.TemporaryDirectory(prefix="exphttp-browser-smoke-") as tmpdir:
        temp_root = Path(tmpdir)
        normal_root = temp_root / "normal"
        unavailable_root = temp_root / "notepad-unavailable"
        normal_root.mkdir(parents=True, exist_ok=True)
        unavailable_root.mkdir(parents=True, exist_ok=True)
        work_dir = temp_root / "playwright"
        work_dir.mkdir(parents=True, exist_ok=True)
        config_path = work_dir / "cli.config.json"
        local_smoke_script = work_dir / smoke_script.name
        upload_fixture = work_dir / "browser-smoke-upload.txt"
        opsec_upload_url_boundary_fixture = (
            work_dir / "browser-smoke-opsec-url-no-switch-boundary.bin"
        )
        opsec_upload_fixture = work_dir / "browser-smoke-opsec-auto-switch-small.bin"
        opsec_upload_boundary_fixture = work_dir / "browser-smoke-opsec-no-switch-boundary.bin"
        opsec_upload_large_fixture = work_dir / "browser-smoke-opsec-auto-switch-large.bin"
        _write_cli_config(config_path)
        upload_fixture.write_text("browser smoke upload\n", encoding="utf-8")
        opsec_upload_url_boundary_fixture.write_bytes(b"U" * 1125)
        opsec_upload_fixture.write_bytes(b"A" * 1126)
        opsec_upload_boundary_fixture.write_bytes(b"C" * 18000)
        opsec_upload_large_fixture.write_bytes(b"B" * 18001)

        live = _LiveServer(server_cls, normal_root, profile=profile)
        unavailable_live = (
            _LiveServer(server_cls, unavailable_root, profile=profile, disable_ecdh=True)
            if smoke_mode == "full"
            else None
        )
        try:
            live.start()
            if unavailable_live is not None:
                unavailable_live.start()
            url = f"http://127.0.0.1:{live.port}/"
            unavailable_url = (
                f"http://127.0.0.1:{unavailable_live.port}/" if unavailable_live is not None else ""
            )
            smoke_source = smoke_script.read_text(encoding="utf-8").replace(
                "__EXPHTTP_BASE_URL__",
                json.dumps(url),
                1,
            )
            smoke_source = smoke_source.replace(
                "__EXPHTTP_UNAVAILABLE_URL__",
                json.dumps(unavailable_url),
                1,
            )
            smoke_source = smoke_source.replace(
                "__EXPHTTP_SMOKE_PROFILE__",
                json.dumps(profile),
                1,
            )
            smoke_source = smoke_source.replace(
                "__EXPHTTP_SMOKE_MODE__",
                json.dumps(smoke_mode),
                1,
            )
            smoke_source = smoke_source.replace(
                "__EXPHTTP_UPLOAD_FILE__",
                json.dumps(str(upload_fixture)),
                1,
            )
            smoke_source = smoke_source.replace(
                "__EXPHTTP_OPSEC_UPLOAD_URL_BOUNDARY_FILE__",
                json.dumps(str(opsec_upload_url_boundary_fixture)),
                1,
            )
            smoke_source = smoke_source.replace(
                "__EXPHTTP_OPSEC_UPLOAD_FILE__",
                json.dumps(str(opsec_upload_fixture)),
                1,
            )
            smoke_source = smoke_source.replace(
                "__EXPHTTP_OPSEC_UPLOAD_BOUNDARY_FILE__",
                json.dumps(str(opsec_upload_boundary_fixture)),
                1,
            )
            smoke_source = smoke_source.replace(
                "__EXPHTTP_OPSEC_UPLOAD_LARGE_FILE__",
                json.dumps(str(opsec_upload_large_fixture)),
                1,
            )
            local_smoke_script.write_text(smoke_source, encoding="utf-8")
            _run_playwright(
                playwright,
                session,
                "open",
                "about:blank",
                "--config",
                str(config_path),
                cwd=REPO_ROOT,
            )
            raw_output = _run_playwright(
                playwright,
                session,
                "--raw",
                "run-code",
                "--filename",
                str(local_smoke_script),
                cwd=REPO_ROOT,
            )
            result = _parse_playwright_json(raw_output)
            result["serverModulePath"] = str(server_module_path)
            result["serverProfile"] = profile
            result["smokeMode"] = smoke_mode
            return result
        finally:
            try:
                _run_playwright(playwright, session, "close", cwd=REPO_ROOT)
            except Exception:
                pass
            if unavailable_live is not None:
                unavailable_live.stop()
            live.stop()


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run the exphttp browser smoke flow")
    parser.add_argument(
        "--installed-package",
        action="store_true",
        help="Import exphttp from the active environment instead of the source checkout.",
    )
    parser.add_argument(
        "--profile",
        choices=SMOKE_PROFILES,
        default="lab",
        help=(
            "Server feature profile to smoke. The default lab profile runs the full flow; "
            "serve/workspace run minimal disabled-state checks."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=SMOKE_MODES,
        default="auto",
        help="Smoke depth: auto selects full for lab and disabled-state for serve/workspace.",
    )
    args = parser.parse_args(argv)

    try:
        result = run_browser_smoke(
            installed_package=args.installed_package,
            profile=args.profile,
            mode=args.mode,
        )
    except Exception as exc:
        print(f"Browser smoke failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

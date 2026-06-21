"""Static checks for operator deployment and release artifacts."""

from __future__ import annotations

import subprocess
from pathlib import Path

from src.settings import load_settings_file

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_systemd_public_direct_config_and_unit_are_valid() -> None:
    config_path = REPO_ROOT / "deploy/systemd/exphttp.ini.example"
    service_path = REPO_ROOT / "deploy/systemd/exphttp.service"

    settings = load_settings_file(config_path)
    settings.validate()

    assert settings.public_direct is True
    assert settings.auth_file == "/etc/exphttp/auth"
    assert settings.profile == "workspace"
    assert settings.body_memory_budget_mb is not None

    service = service_path.read_text(encoding="utf-8")
    assert (
        "ExecStartPre=/opt/exphttp/venv/bin/exphttp "
        "--config /etc/exphttp/exphttp.ini --check-config"
    ) in service
    assert "ExecStart=/opt/exphttp/venv/bin/exphttp --config /etc/exphttp/exphttp.ini" in service
    assert "AmbientCapabilities=CAP_NET_BIND_SERVICE" in service
    assert "NoNewPrivileges=true" in service


def test_systemd_install_script_has_valid_shell_syntax() -> None:
    script_path = REPO_ROOT / "deploy/systemd/install-systemd.sh"

    result = subprocess.run(
        ["bash", "-n", str(script_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_docker_public_direct_compose_uses_ghcr_image_and_config() -> None:
    compose_path = REPO_ROOT / "deploy/docker/docker-compose.public-direct.yml"
    config_path = REPO_ROOT / "deploy/docker/exphttp.ini.example"

    settings = load_settings_file(config_path)
    settings.validate()

    assert settings.public_direct is True
    assert settings.host == "0.0.0.0"
    assert settings.port == 8443
    assert settings.acme_http_port == 8080
    assert settings.auth_file == "/run/secrets/exphttp_auth"

    compose = compose_path.read_text(encoding="utf-8")
    assert "ghcr.io/gkumurzhi/exphttp" in compose
    assert "--config" in compose
    assert "/etc/exphttp/exphttp.ini" in compose
    assert "exphttp_auth:" in compose
    assert "80:8080" in compose
    assert "443:8443" in compose


def test_release_workflow_publishes_pypi_and_ghcr_with_attestations() -> None:
    workflow = (REPO_ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    assert "packages: write" in workflow
    assert "pypa/gh-action-pypi-publish" in workflow
    assert "ghcr.io/gkumurzhi/exphttp" in workflow
    assert "docker/build-push-action" in workflow
    assert "sbom: true" in workflow
    assert "provenance: true" in workflow
    assert "actions/attest-build-provenance" in workflow
    assert "src.config.__version__" in workflow

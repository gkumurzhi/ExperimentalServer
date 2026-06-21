"""Tests for operator-facing configuration loading and validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.settings import (
    ServerSettings,
    SettingsError,
    load_settings_file,
    load_settings_text,
    resolve_settings,
    sample_config_text,
)


def test_default_settings_match_cli_runtime_defaults() -> None:
    settings = ServerSettings()

    assert settings.host == "127.0.0.1"
    assert settings.port == 8080
    assert settings.root_dir == "."
    assert settings.profile == "workspace"
    assert settings.max_size_mb == 100
    assert settings.workers == 10

    kwargs = settings.to_server_kwargs()
    assert kwargs["host"] == "127.0.0.1"
    assert kwargs["port"] == 8080
    assert kwargs["root_dir"] == "."
    assert kwargs["profile"] == "workspace"
    assert kwargs["max_upload_size"] == 100 * 1024 * 1024
    assert kwargs["max_workers"] == 10


def test_ini_file_env_and_cli_precedence(tmp_path: Path) -> None:
    config_file = tmp_path / "exphttp.ini"
    config_file.write_text(
        """
        [server]
        host = 0.0.0.0
        port = 9000
        dir = /srv/exphttp
        profile = serve

        [limits]
        max_size_mb = 64
        body_memory_budget_mb = 256

        [security]
        auth_file = /etc/exphttp/auth
        """,
        encoding="utf-8",
    )

    file_settings = load_settings_file(config_file)
    settings = resolve_settings(
        file_settings=file_settings,
        env={"EXPHTTP_PORT": "9443", "EXPHTTP_PROFILE": "workspace"},
        cli_values={"host": "127.0.0.1"},
    )

    assert settings.host == "127.0.0.1"
    assert settings.port == 9443
    assert settings.root_dir == "/srv/exphttp"
    assert settings.profile == "workspace"
    assert settings.max_size_mb == 64
    assert settings.body_memory_budget_mb == 256
    assert settings.auth_file == "/etc/exphttp/auth"


def test_public_direct_requires_real_tls_auth_file_and_memory_budget() -> None:
    settings = ServerSettings(
        host="0.0.0.0",
        port=443,
        public_direct=True,
        tls=True,
        auth_file="/etc/exphttp/auth",
        body_memory_budget_mb=512,
        profile="workspace",
    )

    with pytest.raises(SettingsError, match="real TLS"):
        settings.validate()

    settings = ServerSettings(
        host="0.0.0.0",
        port=443,
        public_direct=True,
        sslip=True,
        body_memory_budget_mb=512,
        profile="workspace",
    )

    with pytest.raises(SettingsError, match="auth_file"):
        settings.validate()


def test_public_direct_secure_sslip_profile_validates() -> None:
    settings = ServerSettings(
        host="0.0.0.0",
        port=443,
        public_direct=True,
        sslip=True,
        auth_file="/etc/exphttp/auth",
        body_memory_budget_mb=512,
        profile="workspace",
    )

    settings.validate()
    kwargs = settings.to_server_kwargs()
    assert kwargs["tls"] is True
    assert kwargs["sslip"] is True
    assert kwargs["auth_file"] == "/etc/exphttp/auth"
    assert kwargs["body_memory_budget"] == 512 * 1024 * 1024


def test_public_direct_rejects_lab_and_plugins_without_explicit_allowance() -> None:
    lab_settings = ServerSettings(
        public_direct=True,
        sslip=True,
        auth_file="/etc/exphttp/auth",
        body_memory_budget_mb=512,
        profile="lab",
    )
    with pytest.raises(SettingsError, match="profile"):
        lab_settings.validate()

    plugin_settings = ServerSettings(
        public_direct=True,
        sslip=True,
        auth_file="/etc/exphttp/auth",
        body_memory_budget_mb=512,
        plugin_allowlist=("demo_plugin",),
    )
    with pytest.raises(SettingsError, match="plugins"):
        plugin_settings.validate()


def test_redacted_json_does_not_expose_inline_auth_secret() -> None:
    settings = ServerSettings(auth="admin:secret", auth_file="/etc/exphttp/auth")

    rendered = json.dumps(settings.to_redacted_dict())

    assert "secret" not in rendered
    assert '"auth": "***"' in rendered
    assert "/etc/exphttp/auth" in rendered


def test_sample_config_is_parseable() -> None:
    config = sample_config_text()

    settings = load_settings_text(config)

    assert settings.public_direct is True
    assert settings.profile == "workspace"
    assert settings.auth_file == "/etc/exphttp/auth"

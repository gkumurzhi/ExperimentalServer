"""Tests for the public exphttp plugin API."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.extensions import HandlerContext, PluginMethodSpec, PluginSpec
from src.http import HTTPRequest, HTTPResponse
from src.server import ExperimentalHTTPServer


def _request(method: str, path: str = "/") -> HTTPRequest:
    return HTTPRequest(f"{method} {path} HTTP/1.1\r\nHost: example.test\r\n\r\n".encode("ascii"))


def test_plugin_method_registers_and_dispatches(temp_dir: Path) -> None:
    def handler(request: HTTPRequest, context: HandlerContext) -> HTTPResponse:
        response = HTTPResponse(200)
        response.set_body(
            f"{request.method}:{context.profile}:{context.plugin_name}".encode(),
            "text/plain",
        )
        return response

    plugin = PluginSpec(
        name="demo",
        methods=(
            PluginMethodSpec(
                method="ECHO",
                handler=handler,
                mutating=False,
                cors_allowed=True,
                profiles=("workspace",),
            ),
        ),
    )

    server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, plugins=[plugin])

    assert "ECHO" in server.method_handlers
    assert server.plugin_methods == {"ECHO": "demo"}
    response = server._dispatch_handler(_request("ECHO"))
    assert response.status_code == 200
    assert response.body == b"ECHO:workspace:demo"

    ping = json.loads(server.handle_ping(_request("PING")).body.decode("utf-8"))
    assert ping["plugin_methods"] == ["ECHO"]


def test_public_exphttp_extensions_exports_plugin_api() -> None:
    from exphttp.extensions import PluginMethodSpec as PublicPluginMethodSpec
    from exphttp.extensions import PluginSpec as PublicPluginSpec

    assert PublicPluginMethodSpec is PluginMethodSpec
    assert PublicPluginSpec is PluginSpec


def test_plugin_method_cannot_override_core_method_by_default(temp_dir: Path) -> None:
    plugin = PluginSpec(
        name="bad",
        methods=(
            PluginMethodSpec(
                method="GET",
                handler=lambda _request, _context: HTTPResponse(200),
            ),
        ),
    )

    with pytest.raises(ValueError, match="core method"):
        ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, plugins=[plugin])


def test_plugin_method_cannot_reuse_disabled_builtin_name_without_override(temp_dir: Path) -> None:
    plugin = PluginSpec(
        name="shadow-smuggle",
        methods=(
            PluginMethodSpec(
                method="SMUGGLE",
                handler=lambda _request, _context: HTTPResponse(200),
                profiles=("workspace",),
            ),
        ),
    )

    with pytest.raises(ValueError, match="core method"):
        ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, plugins=[plugin])


def test_plugin_method_can_override_disabled_builtin_name_when_enabled(temp_dir: Path) -> None:
    plugin = PluginSpec(
        name="shadow-smuggle",
        methods=(
            PluginMethodSpec(
                method="SMUGGLE",
                handler=lambda _request, _context: HTTPResponse(200),
                profiles=("workspace",),
            ),
        ),
    )

    server = ExperimentalHTTPServer(
        root_dir=str(temp_dir),
        quiet=True,
        plugins=[plugin],
        plugins_override_core=True,
    )

    assert server.plugin_methods == {"SMUGGLE": "shadow-smuggle"}
    response = server._dispatch_handler(_request("SMUGGLE"))
    assert response.status_code == 200


def test_plugin_method_profile_gating(temp_dir: Path) -> None:
    plugin = PluginSpec(
        name="lab-only",
        methods=(
            PluginMethodSpec(
                method="LABX",
                handler=lambda _request, _context: HTTPResponse(200),
                profiles=("lab",),
            ),
        ),
    )

    workspace_server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, plugins=[plugin])
    lab_server = ExperimentalHTTPServer(
        root_dir=str(temp_dir),
        quiet=True,
        profile="lab",
        plugins=[plugin],
    )

    assert "LABX" not in workspace_server.method_handlers
    assert "LABX" in lab_server.method_handlers


def test_mutating_plugin_method_uses_browser_mutation_guard(temp_dir: Path) -> None:
    plugin = PluginSpec(
        name="mutator",
        methods=(
            PluginMethodSpec(
                method="BURN",
                handler=lambda _request, _context: HTTPResponse(204),
                mutating=True,
                cors_allowed=True,
            ),
        ),
    )
    server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, plugins=[plugin])

    assert server._is_browser_protected_mutation(_request("BURN")) is True


def test_plugin_cors_policy_exposes_only_cors_allowed_methods(temp_dir: Path) -> None:
    plugin = PluginSpec(
        name="cors-demo",
        methods=(
            PluginMethodSpec(
                method="SAFEPLUGIN",
                handler=lambda _request, _context: HTTPResponse(200),
                mutating=False,
                cors_allowed=True,
            ),
            PluginMethodSpec(
                method="INTERNALPLUGIN",
                handler=lambda _request, _context: HTTPResponse(200),
                mutating=False,
                cors_allowed=False,
            ),
        ),
    )
    server = ExperimentalHTTPServer(root_dir=str(temp_dir), quiet=True, plugins=[plugin])

    methods = server._cors_allow_methods_header().split(", ")

    assert "SAFEPLUGIN" in methods
    assert "INTERNALPLUGIN" not in methods

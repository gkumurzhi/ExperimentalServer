"""Tests for the active-documentation stale contract checker."""

from __future__ import annotations

from pathlib import Path

from tools import check_stale_docs


def write_minimal_docs(root: Path) -> None:
    """Create the files and directories used by the default stale-doc scan."""
    (root / "docs").mkdir()
    (root / "examples").mkdir()
    (root / "README.md").write_text("# README\n", encoding="utf-8")
    (root / "API.md").write_text("# API\n", encoding="utf-8")
    (root / "CLAUDE.md").write_text("# CLAUDE\n", encoding="utf-8")
    (root / "docs" / "api.md").write_text("# API mirror\n", encoding="utf-8")
    (root / "examples" / "basic_file_server.sh").write_text(
        "#!/usr/bin/env bash\n",
        encoding="utf-8",
    )


def test_historical_changelog_text_is_allowed(tmp_path: Path) -> None:
    write_minimal_docs(tmp_path)
    stale_history = (
        "- **Behavior:** advanced upload is enabled by default; unknown non-standard methods "
        "carrying body data are accepted as uploads\n"
    )
    (tmp_path / "CHANGELOG.md").write_text(stale_history, encoding="utf-8")
    (tmp_path / "docs" / "changelog.md").write_text(stale_history, encoding="utf-8")

    assert check_stale_docs.find_stale_references(tmp_path) == []


def test_active_stale_reference_is_reported(tmp_path: Path) -> None:
    write_minimal_docs(tmp_path)
    (tmp_path / "README.md").write_text("Set X-HMAC when creating notes.\n", encoding="utf-8")

    findings = check_stale_docs.find_stale_references(tmp_path)

    assert len(findings) == 1
    assert findings[0].path == Path("README.md")
    assert findings[0].line_number == 1
    assert "removed Secure Notepad HMAC header" in findings[0].message


def test_active_crypto_extra_guidance_is_reported(tmp_path: Path) -> None:
    write_minimal_docs(tmp_path)
    (tmp_path / "CONTRIBUTING.md").write_text(
        'pip install -e ".[crypto,dev,lint,test]"\n',
        encoding="utf-8",
    )

    findings = check_stale_docs.find_stale_references(tmp_path)

    assert len(findings) == 1
    assert findings[0].path == Path("CONTRIBUTING.md")
    assert "compatibility-only `crypto` extra" in findings[0].message


def test_active_ui_crypto_extra_remediation_is_reported(tmp_path: Path) -> None:
    write_minimal_docs(tmp_path)
    ui_path = tmp_path / "src" / "data" / "static" / "ui" / "core.js"
    ui_path.parent.mkdir(parents=True)
    ui_path.write_text(
        'notepadUnavailableServer: "Notepad unavailable: exphttp[crypto] required."\n',
        encoding="utf-8",
    )

    findings = check_stale_docs.find_stale_references(tmp_path)

    assert len(findings) == 1
    assert findings[0].path == Path("src/data/static/ui/core.js")
    assert "stale crypto extra remediation" in findings[0].message


def test_active_package_crypto_extra_variant_is_reported(tmp_path: Path) -> None:
    write_minimal_docs(tmp_path)
    (tmp_path / "README.md").write_text(
        "pip install exphttp[crypto,dev]\n",
        encoding="utf-8",
    )

    findings = check_stale_docs.find_stale_references(tmp_path)

    assert len(findings) == 1
    assert findings[0].path == Path("README.md")
    assert "stale crypto extra remediation" in findings[0].message


def test_public_exposure_quick_start_wording_is_reported(tmp_path: Path) -> None:
    write_minimal_docs(tmp_path)
    (tmp_path / "README.md").write_text(
        "exphttp -H 0.0.0.0 -p 443     # Публичный доступ\n",
        encoding="utf-8",
    )

    findings = check_stale_docs.find_stale_references(tmp_path)

    assert findings
    assert {finding.path for finding in findings} == {Path("README.md")}
    assert any("public-exposure quick-start" in finding.message for finding in findings)


def test_threat_model_duplicate_content_length_wording_is_reported(tmp_path: Path) -> None:
    write_minimal_docs(tmp_path)
    (tmp_path / "docs" / "threat-model.md").write_text(
        "| Content-Length smuggling (duplicate/negative CL) | Rejected |\n",
        encoding="utf-8",
    )

    findings = check_stale_docs.find_stale_references(tmp_path)

    assert len(findings) == 1
    assert findings[0].path == Path("docs/threat-model.md")
    assert "identical duplicates are accepted" in findings[0].message


def test_public_src_import_guidance_is_reported(tmp_path: Path) -> None:
    write_minimal_docs(tmp_path)
    (tmp_path / "README.md").write_text(
        "python -m src --help\nfrom src import ExperimentalHTTPServer\n",
        encoding="utf-8",
    )

    findings = check_stale_docs.find_stale_references(tmp_path)

    assert len(findings) == 2
    assert {finding.path for finding in findings} == {Path("README.md")}
    assert any("python -m exphttp" in finding.message for finding in findings)
    assert any("from exphttp" in finding.message for finding in findings)


def test_semantic_contract_requires_final_api_metrics(tmp_path: Path) -> None:
    write_minimal_docs(tmp_path)
    (tmp_path / "API.md").write_text(
        '  "metrics": {"websocket": {"active": 0}}\n',
        encoding="utf-8",
    )

    findings = check_stale_docs.find_semantic_contract_issues(tmp_path, ("API.md",))

    assert any("operational metrics" in finding.message for finding in findings)


def test_main_returns_failure_with_actionable_output(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    write_minimal_docs(tmp_path)
    (tmp_path / "examples" / "legacy.md").write_text("Run exphttp --root /srv.\n", encoding="utf-8")
    monkeypatch.setattr(check_stale_docs, "REPO_ROOT", tmp_path)

    assert check_stale_docs.main([]) == 1

    captured = capsys.readouterr()
    assert "Found stale documented contract references" in captured.err
    assert "examples/legacy.md:1" in captured.err
    assert "legacy CLI flag `--root`; use `--dir`" in captured.err

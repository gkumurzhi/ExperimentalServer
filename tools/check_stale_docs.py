#!/usr/bin/env python3
"""Fail when active docs, UI strings, and smoke checks contain stale references."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_TARGETS: tuple[str, ...] = (
    "README.md",
    "API.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "mkdocs.yml",
    "docs",
    "examples",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/workflows",
    "src/request_pipeline.py",
    "src/handlers/notepad.py",
    "src/data/static/ui/core.js",
    "tools/browser_smoke.playwright.js",
    "tools/browser_smoke.py",
)

HISTORICAL_PATHS: frozenset[Path] = frozenset(
    {
        Path("CHANGELOG.md"),
        Path("docs/changelog.md"),
    }
)

SKIPPED_DIRS: frozenset[str] = frozenset({"__pycache__"})


@dataclass(frozen=True)
class StalePattern:
    """One stale public contract reference to reject in active documentation."""

    regex: re.Pattern[str]
    message: str


@dataclass(frozen=True)
class SemanticRequirement:
    """One required active documentation contract."""

    path: Path
    regex: re.Pattern[str]
    message: str


@dataclass(frozen=True)
class Finding:
    """One stale reference found in an active documentation file."""

    path: Path
    line_number: int
    line: str
    message: str


STALE_PATTERNS: tuple[StalePattern, ...] = (
    StalePattern(re.compile(r"--root\b"), "legacy CLI flag `--root`; use `--dir`"),
    StalePattern(re.compile(r"--max-upload\b"), "legacy CLI flag `--max-upload`; use `--max-size`"),
    StalePattern(re.compile(r"/notes/pubkey\b"), "removed Notepad public-key endpoint"),
    StalePattern(re.compile(r"\bX-Enc-Key\b"), "removed Secure Notepad encrypted key header"),
    StalePattern(re.compile(r"\bX-HMAC\b"), "removed Secure Notepad HMAC header"),
    StalePattern(re.compile(r"--no-info\b"), "removed CLI flag `--no-info`"),
    StalePattern(re.compile(r"--opsec\b"), "removed CLI flag `--opsec`"),
    StalePattern(re.compile(r"--sandbox\b"), "removed CLI flag `--sandbox`"),
    StalePattern(
        re.compile(r"advanced upload is enabled by default"),
        "stale advanced-upload default wording",
    ),
    StalePattern(
        re.compile(r"ciphertext \+ metadata"),
        "stale Notepad recoverability wording",
    ),
    StalePattern(
        re.compile(r"exphttp\[[^\]\n]*\bcrypto\b[^\]\n]*\]"),
        "stale crypto extra remediation; repair the default runtime install instead",
    ),
    StalePattern(
        re.compile(r'\.\[[^"\]\n]*crypto[^"\]\n]*\]'),
        "stale active install command with compatibility-only `crypto` extra",
    ),
    StalePattern(
        re.compile(r"zero external dependencies", re.IGNORECASE),
        "stale zero-dependency runtime wording",
    ),
    StalePattern(
        re.compile(r"\bpure Python\b", re.IGNORECASE),
        "stale pure-Python runtime wording",
    ),
    StalePattern(
        re.compile(r"чистом Python без внешних зависимостей", re.IGNORECASE),
        "stale zero-dependency runtime wording",
    ),
    StalePattern(
        re.compile(r"Optional cryptography", re.IGNORECASE),
        "stale optional-cryptography wording; crypto is a default runtime dependency",
    ),
    StalePattern(
        re.compile(r"Публичный доступ(?:\s+на порту 443)?", re.IGNORECASE),
        "stale public-exposure quick-start wording; document external prerequisites",
    ),
    StalePattern(
        re.compile(r"Public access(?:\s+on port 443)?", re.IGNORECASE),
        "stale public-exposure quick-start wording; document external prerequisites",
    ),
    StalePattern(
        re.compile(r"exphttp[^\n]*-H\s+0\.0\.0\.0[^\n]*#\s*(?:Публичный доступ|public access)"),
        "stale public-exposure bind example; document trusted-lab/external prerequisites",
    ),
    StalePattern(
        re.compile(r"Обход DLP/прокси", re.IGNORECASE),
        "stale lab-only SMUGGLE framing; avoid bypass/delivery wording",
    ),
    StalePattern(
        re.compile(r"\bDLP/proxy bypass\b", re.IGNORECASE),
        "stale lab-only SMUGGLE framing; avoid bypass/delivery wording",
    ),
    StalePattern(
        re.compile(
            r"(?:через\s+email\s+и\s+мессендж\w+|via\s+email\s+and\s+messengers|email(?:,|\s+and)\s+messengers)",
            re.IGNORECASE,
        ),
        "stale lab-only SMUGGLE framing; avoid third-party delivery wording",
    ),
    StalePattern(
        re.compile(r"Content-Length smuggling \(duplicate/negative CL\)", re.IGNORECASE),
        (
            "stale Content-Length wording; identical duplicates are accepted, "
            "conflicting values are rejected"
        ),
    ),
    StalePattern(
        re.compile(r"\bpython\s+-m\s+src(?:\b|\.)"),
        "stale public module command `python -m src`; use `python -m exphttp`",
    ),
    StalePattern(
        re.compile(r"\bfrom\s+src\s+import\b"),
        "stale public import path `from src`; use `from exphttp`",
    ),
    StalePattern(
        re.compile(r"(?<![\w.])import\s+src\b"),
        "stale public import path `import src`; use `import exphttp`",
    ),
    StalePattern(
        re.compile(
            r"It is artifact-only:\s*it does not publish to PyPI,\s*GHCR,\s*or another registry",
            re.IGNORECASE,
        ),
        "stale artifact-only release wording; tagged releases publish PyPI and GHCR",
    ),
    StalePattern(
        re.compile(
            r"Release workflows currently produce signed GitHub Actions artifacts only",
            re.IGNORECASE,
        ),
        "stale artifact-only release wording; tagged releases publish PyPI and GHCR",
    ),
)

SEMANTIC_REQUIREMENTS: tuple[SemanticRequirement, ...] = (
    SemanticRequirement(
        Path("README.md"),
        re.compile(r"Режимы эксплуатации", re.IGNORECASE),
        "README must separate localhost, trusted-lab, and external-exposure modes",
    ),
    SemanticRequirement(
        Path("README.md"),
        re.compile(r"legacy v0[\s\S]+/api/v1", re.IGNORECASE),
        (
            "README must describe the current HTTP/WebSocket surface as legacy v0 "
            "and note that `/api/v1` is not implemented"
        ),
    ),
    SemanticRequirement(
        Path("README.md"),
        re.compile(r"не делает сервис\s+безопасным для произвольного интернета", re.IGNORECASE),
        "README must not imply binding/TLS/Auth alone make arbitrary internet exposure safe",
    ),
    SemanticRequirement(
        Path("SECURITY.md"),
        re.compile(r"External exposure baseline", re.IGNORECASE),
        "SECURITY must define a minimum external-exposure hardening baseline",
    ),
    SemanticRequirement(
        Path("SECURITY.md"),
        re.compile(
            r"does\s+not\s+persist\s+the\s+client-derived\s+AES\s+key[\s\S]+durable\s+recovery\s+out\s+of\s+scope",
            re.IGNORECASE,
        ),
        "SECURITY must state that Secure Notepad does not persist durable recovery material today",
    ),
    SemanticRequirement(
        Path("API.md"),
        re.compile(r"Request Framing and Caps", re.IGNORECASE),
        "API docs must describe receive-layer header/body caps and framing behavior",
    ),
    SemanticRequirement(
        Path("API.md"),
        re.compile(
            r"bytes_received[\s\S]+request_latency_ms[\s\S]+worker",
            re.IGNORECASE,
        ),
        "API docs must include finalized operational metrics fields",
    ),
    SemanticRequirement(
        Path("API.md"),
        re.compile(r"Notepad-specific encrypted blob limit", re.IGNORECASE),
        "API docs must describe the finalized Notepad encrypted-blob limit",
    ),
    SemanticRequirement(
        Path("API.md"),
        re.compile(r"Sec-Fetch-Site: cross-site", re.IGNORECASE),
        "API docs must describe the browser-origin mutation policy",
    ),
    SemanticRequirement(
        Path("API.md"),
        re.compile(
            r"script-src\s+'self'[\s\S]+style-src\s+'self'\s+'unsafe-inline'",
            re.IGNORECASE,
        ),
        "API docs must describe the current HTML CSP contract",
    ),
    SemanticRequirement(
        Path("docs/threat-model.md"),
        re.compile(
            r"Conflicting Content-Length values are rejected; duplicate identical "
            r"Content-Length values are accepted",
            re.IGNORECASE,
        ),
        "threat model must distinguish conflicting from identical duplicate Content-Length",
    ),
)


def relative_to_root(path: Path, repo_root: Path) -> Path:
    """Return *path* relative to *repo_root* when possible."""
    try:
        return path.relative_to(repo_root)
    except ValueError:
        return path


def is_skipped(path: Path, repo_root: Path) -> bool:
    """Return whether *path* should be ignored by the active-doc scanner."""
    relative = relative_to_root(path, repo_root)
    return relative in HISTORICAL_PATHS or any(part in SKIPPED_DIRS for part in relative.parts)


def expand_target(target: Path, repo_root: Path) -> Iterable[Path]:
    """Yield text-file candidates for one configured target path."""
    if not target.exists() or is_skipped(target, repo_root):
        return
    if target.is_file():
        yield target
        return
    for child in sorted(target.rglob("*")):
        if child.is_file() and not is_skipped(child, repo_root):
            yield child


def iter_check_paths(repo_root: Path, targets: Sequence[str] = DEFAULT_TARGETS) -> Iterable[Path]:
    """Yield active documentation and example files that should be checked."""
    for target in targets:
        target_path = Path(target)
        if not target_path.is_absolute():
            target_path = repo_root / target_path
        yield from expand_target(target_path, repo_root)


def scan_file(path: Path, repo_root: Path) -> list[Finding]:
    """Return stale-reference findings for one file."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return []

    findings: list[Finding] = []
    relative = relative_to_root(path, repo_root)
    for line_number, line in enumerate(lines, start=1):
        for stale_pattern in STALE_PATTERNS:
            if stale_pattern.regex.search(line):
                findings.append(
                    Finding(
                        path=relative,
                        line_number=line_number,
                        line=line.strip(),
                        message=stale_pattern.message,
                    )
                )
    return findings


def find_stale_references(
    repo_root: Path = REPO_ROOT,
    targets: Sequence[str] = DEFAULT_TARGETS,
) -> list[Finding]:
    """Return all stale references in active docs/examples under *repo_root*."""
    return [
        finding
        for path in iter_check_paths(repo_root, targets)
        for finding in scan_file(path, repo_root)
    ]


def find_semantic_contract_issues(
    repo_root: Path = REPO_ROOT,
    targets: Sequence[str] = DEFAULT_TARGETS,
) -> list[Finding]:
    """Return missing semantic documentation contracts for active targets."""
    covered_paths = {
        relative_to_root(path, repo_root) for path in iter_check_paths(repo_root, targets)
    }
    findings: list[Finding] = []

    for requirement in SEMANTIC_REQUIREMENTS:
        if requirement.path not in covered_paths:
            continue
        path = repo_root / requirement.path
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        if requirement.regex.search(text):
            continue

        findings.append(
            Finding(
                path=requirement.path,
                line_number=1,
                line="<missing required semantic documentation>",
                message=requirement.message,
            )
        )

    return findings


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Check active documentation, UI strings, and smoke checks for stale references. "
            "Historical changelog files are intentionally ignored."
        )
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="optional files or directories to scan instead of the default active docs/examples",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point."""
    args = parse_args(argv)
    targets = tuple(args.targets) if args.targets else DEFAULT_TARGETS
    findings = find_stale_references(REPO_ROOT, targets)
    findings.extend(find_semantic_contract_issues(REPO_ROOT, targets))

    if not findings:
        print("No stale documented contract references found.")
        return 0

    print("Found stale documented contract references:", file=sys.stderr)
    for finding in findings:
        print(
            f"  - {finding.path}:{finding.line_number}: {finding.message}: {finding.line}",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

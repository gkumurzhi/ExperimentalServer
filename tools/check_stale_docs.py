#!/usr/bin/env python3
"""Fail when active docs/examples contain stale public contract references."""

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
    "docs",
    "examples",
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


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Check active documentation and examples for stale public contract references. "
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

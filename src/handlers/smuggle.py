"""
HTML Smuggling handler.
"""

import json
import logging
import secrets
import time
from dataclasses import dataclass
from pathlib import Path

from ..http import HTTPRequest, HTTPResponse
from ..utils.captcha import generate_password_captcha
from ..utils.smuggling import (
    SAFE_SMUGGLE_EXTENSIONS,
    SAFE_SMUGGLE_PRESETS,
    SafeSmuggleBuilderConfig,
    generate_smuggling_html,
)
from .base import BaseHandler

logger = logging.getLogger("httpserver")

SMUGGLE_SOURCE_SIZE_LIMIT = 10 * 1024 * 1024
DEFAULT_SMUGGLE_TEMP_MAX_AGE_SECONDS = 3600
DEFAULT_SMUGGLE_TEMP_MAX_FILES = 32
DEFAULT_SMUGGLE_TEMP_MAX_BYTES = 128 * 1024 * 1024
SMUGGLE_BUILDER_MAX_DOWNLOAD_NAME = 120
SMUGGLE_BUILDER_MAX_TITLE = 120
SMUGGLE_BUILDER_MAX_MESSAGE = 280
SMUGGLE_BUILDER_MAX_CTA_LABEL = 80
SMUGGLE_BUILDER_MAX_DELAY_MS = 10_000


@dataclass(frozen=True, slots=True)
class SmuggleTempPolicy:
    """Retention policy for generated one-shot SMUGGLE HTML artifacts."""

    max_age_seconds: float | None = DEFAULT_SMUGGLE_TEMP_MAX_AGE_SECONDS
    max_file_count: int | None = DEFAULT_SMUGGLE_TEMP_MAX_FILES
    max_total_bytes: int | None = DEFAULT_SMUGGLE_TEMP_MAX_BYTES

    def __post_init__(self) -> None:
        if self.max_age_seconds is not None and self.max_age_seconds < 0:
            raise ValueError("smuggle_temp_max_age must be at least 0")
        if self.max_file_count is not None and self.max_file_count < 0:
            raise ValueError("smuggle_temp_file_limit must be at least 0")
        if self.max_total_bytes is not None and self.max_total_bytes < 0:
            raise ValueError("smuggle_temp_storage_limit must be at least 0")


@dataclass(frozen=True, slots=True)
class SmuggleTempArtifact:
    """Current generated SMUGGLE file metadata."""

    path: Path
    size: int
    mtime: float


@dataclass(frozen=True, slots=True)
class SmuggleTempUsage:
    """Current retained SMUGGLE temp usage."""

    total_bytes: int
    file_count: int


class SmuggleTempQuotaExceeded(Exception):
    """Raised when a generated SMUGGLE artifact cannot be retained."""


class SmuggleHandlersMixin(BaseHandler):
    """Mixin with HTML Smuggling handler."""

    smuggle_source_size_limit = SMUGGLE_SOURCE_SIZE_LIMIT
    smuggle_temp_policy: SmuggleTempPolicy

    # Temporary SMUGGLE files attribute (defined in server)
    _temp_smuggle_files: set[str]

    def handle_smuggle(self, request: HTTPRequest) -> HTTPResponse:
        """Custom SMUGGLE method — generate HTML smuggling page.

        Query params:
            encrypt=1 — enable XOR obfuscation (password generated server-side)
        """
        if not self._feature_set().smuggle:
            return self._method_not_allowed(request.method)

        encrypt = request.query_params.get("encrypt") == "1"

        if self._is_hidden_file(request.path):
            response = HTTPResponse(404)
            response.set_body(
                json.dumps({"error": "File not found", "path": request.path}), "application/json"
            )
            return response

        file_path = self._get_file_path(request.path, for_sandbox=True)

        if file_path is None or not file_path.exists() or file_path.is_dir():
            response = HTTPResponse(404)
            response.set_body(
                json.dumps({"error": "File not found", "path": request.path}), "application/json"
            )
            return response

        source_size_limit = self._smuggle_source_size_limit()
        source_size = file_path.stat().st_size
        if source_size > source_size_limit:
            return self._smuggle_too_large_response(source_size, source_size_limit)

        try:
            builder = self._parse_safe_smuggle_builder(request)
        except ValueError as exc:
            return self._bad_request(str(exc))

        # Generate random password server-side if encryption requested
        password = None
        password_captcha = None
        if encrypt:
            # 7 chars: uppercase letters and digits only
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            password = "".join(secrets.choice(alphabet) for _ in range(7))
            # Generate captcha with the password
            password_captcha = generate_password_captcha(password)

        logger.debug(f"SMUGGLE {file_path.name}, encrypt={encrypt}")

        # Read at most one byte past the cap to avoid a race with file growth after stat().
        with file_path.open("rb") as f:
            file_data = f.read(source_size_limit + 1)
        if len(file_data) > source_size_limit:
            return self._smuggle_too_large_response(len(file_data), source_size_limit)

        # Generate HTML
        html = generate_smuggling_html(
            file_data=file_data,
            filename=file_path.name,
            password=password,
            password_captcha=password_captcha,
            builder=builder,
        )

        try:
            temp_path = self._write_smuggle_temp_html(html.encode("utf-8"))
        except SmuggleTempQuotaExceeded as exc:
            logger.warning("SMUGGLE temp artifact rejected by storage policy: %s", exc)
            return self._error_response(507, str(exc))
        except OSError as exc:
            logger.error("SMUGGLE temp artifact write failed: %s", exc)
            return self._error_response(500, "Failed to create SMUGGLE artifact")

        # Return URL to the temp file
        temp_name = temp_path.name
        payload: dict[str, str | bool] = {
            "url": f"/uploads/{temp_name}",
            "file": file_path.name,
            "encrypted": password is not None,
        }
        if password is not None:
            payload["password"] = password

        response = HTTPResponse(200)
        response.set_body(json.dumps(payload), "application/json")
        response.set_header("X-Smuggle-URL", f"/uploads/{temp_name}")

        return response

    def _parse_safe_smuggle_builder(
        self,
        request: HTTPRequest,
    ) -> SafeSmuggleBuilderConfig | None:
        """Parse and validate safe builder query params for SMUGGLE."""
        query = request.query_params
        builder_keys = (
            "download_name",
            "download_ext",
            "preset",
            "title",
            "message",
            "cta_label",
            "delay_ms",
            "show_notice",
        )
        if not any(key in query for key in builder_keys):
            return None

        download_ext = (query.get("download_ext") or "").strip().lstrip(".").lower()
        if download_ext and download_ext not in SAFE_SMUGGLE_EXTENSIONS:
            raise ValueError("Invalid SMUGGLE builder extension")

        preset = (query.get("preset") or "direct").strip().lower()
        if preset not in SAFE_SMUGGLE_PRESETS:
            raise ValueError("Invalid SMUGGLE builder preset")

        raw_delay = (query.get("delay_ms") or "0").strip()
        try:
            delay_ms = int(raw_delay)
        except ValueError as exc:
            raise ValueError("Invalid SMUGGLE builder delay") from exc
        if delay_ms < 0 or delay_ms > SMUGGLE_BUILDER_MAX_DELAY_MS:
            raise ValueError("Invalid SMUGGLE builder delay")

        raw_show_notice = (query.get("show_notice") or "1").strip().lower()
        if raw_show_notice not in {"1", "0", "true", "false", "yes", "no"}:
            raise ValueError("Invalid SMUGGLE builder show_notice")

        return SafeSmuggleBuilderConfig(
            download_name=self._validate_smuggle_builder_text(
                query.get("download_name"),
                field_name="download name",
                max_length=SMUGGLE_BUILDER_MAX_DOWNLOAD_NAME,
            ),
            download_ext=download_ext or None,
            preset=preset,
            title=self._validate_smuggle_builder_text(
                query.get("title"),
                field_name="title",
                max_length=SMUGGLE_BUILDER_MAX_TITLE,
            ),
            message=self._validate_smuggle_builder_text(
                query.get("message"),
                field_name="message",
                max_length=SMUGGLE_BUILDER_MAX_MESSAGE,
            ),
            cta_label=self._validate_smuggle_builder_text(
                query.get("cta_label"),
                field_name="CTA label",
                max_length=SMUGGLE_BUILDER_MAX_CTA_LABEL,
            ),
            delay_ms=delay_ms,
            show_notice=raw_show_notice in {"1", "true", "yes"},
        )

    def _validate_smuggle_builder_text(
        self,
        raw_value: str | None,
        *,
        field_name: str,
        max_length: int,
    ) -> str | None:
        """Return stripped builder text or raise on over-length values."""
        value = (raw_value or "").strip()
        if not value:
            return None
        if len(value) > max_length:
            raise ValueError(f"SMUGGLE builder {field_name} is too long")
        return value

    def _smuggle_source_size_limit(self) -> int:
        """Return the effective SMUGGLE source cap in bytes."""
        configured_limit = int(
            getattr(self, "smuggle_source_size_limit", SMUGGLE_SOURCE_SIZE_LIMIT)
        )
        upload_limit = int(getattr(self, "max_upload_size", configured_limit))
        return min(configured_limit, upload_limit)

    def _smuggle_temp_policy(self) -> SmuggleTempPolicy:
        """Return the effective generated-artifact retention policy."""
        policy = getattr(self, "smuggle_temp_policy", None)
        if isinstance(policy, SmuggleTempPolicy):
            return policy
        return SmuggleTempPolicy()

    def _write_smuggle_temp_html(self, html_bytes: bytes) -> Path:
        """Write and register a generated SMUGGLE artifact under retention limits."""
        with self._smuggle_lock:
            self._ensure_smuggle_temp_capacity_locked(len(html_bytes))
            last_error: FileExistsError | None = None
            for _attempt in range(64):
                temp_path = self.upload_dir / f"smuggle_{secrets.token_hex(8)}.html"
                try:
                    with temp_path.open("xb") as output_file:
                        output_file.write(html_bytes)
                    self._temp_smuggle_files.add(str(temp_path))
                    return temp_path
                except FileExistsError as exc:
                    last_error = exc
                except OSError:
                    temp_path.unlink(missing_ok=True)
                    raise

        raise FileExistsError("Could not reserve a SMUGGLE temp file") from last_error

    def _ensure_smuggle_temp_capacity_locked(self, pending_bytes: int) -> None:
        """Prune old artifacts and raise if a pending artifact still cannot fit."""
        self._cleanup_smuggle_temp_artifacts_locked(pending_bytes=pending_bytes, pending_files=1)
        usage = self._smuggle_temp_usage_locked()
        policy = self._smuggle_temp_policy()

        projected_files = usage.file_count + 1
        if policy.max_file_count is not None and projected_files > policy.max_file_count:
            raise SmuggleTempQuotaExceeded(
                "SMUGGLE temp file count quota exceeded. "
                f"Current files: {usage.file_count}; limit: {policy.max_file_count}."
            )

        projected_bytes = usage.total_bytes + pending_bytes
        if policy.max_total_bytes is not None and projected_bytes > policy.max_total_bytes:
            raise SmuggleTempQuotaExceeded(
                "SMUGGLE temp storage quota exceeded. "
                f"Current usage: {self.format_size(usage.total_bytes)}; "
                f"attempted artifact: {self.format_size(pending_bytes)}; "
                f"limit: {self.format_size(policy.max_total_bytes)}."
            )

    def cleanup_smuggle_temp_artifacts(self, *, remove_all: bool = False) -> int:
        """Clean generated SMUGGLE artifacts and return the number removed."""
        with self._smuggle_lock:
            return self._cleanup_smuggle_temp_artifacts_locked(remove_all=remove_all)

    def _cleanup_smuggle_temp_artifacts_locked(
        self,
        *,
        pending_bytes: int = 0,
        pending_files: int = 0,
        remove_all: bool = False,
    ) -> int:
        """Apply age/count/byte retention to generated SMUGGLE files."""
        artifacts = self._smuggle_temp_artifacts_locked()
        policy = self._smuggle_temp_policy()
        removed = 0

        if remove_all:
            for artifact in artifacts:
                if self._remove_smuggle_temp_artifact_locked(artifact.path):
                    removed += 1
            return removed

        max_age = policy.max_age_seconds
        if max_age is not None:
            now = time.time()
            fresh_artifacts = []
            for artifact in artifacts:
                if now - artifact.mtime > max_age:
                    if self._remove_smuggle_temp_artifact_locked(artifact.path):
                        removed += 1
                else:
                    fresh_artifacts.append(artifact)
            artifacts = fresh_artifacts

        artifacts.sort(key=lambda artifact: artifact.mtime)
        while artifacts and self._smuggle_temp_projection_exceeds_locked(
            artifacts,
            pending_bytes=pending_bytes,
            pending_files=pending_files,
        ):
            artifact = artifacts.pop(0)
            if self._remove_smuggle_temp_artifact_locked(artifact.path):
                removed += 1

        return removed

    def _smuggle_temp_projection_exceeds_locked(
        self,
        artifacts: list[SmuggleTempArtifact],
        *,
        pending_bytes: int,
        pending_files: int,
    ) -> bool:
        """Return True when retained artifacts plus pending file exceed policy."""
        policy = self._smuggle_temp_policy()
        file_count = len(artifacts) + pending_files
        total_bytes = sum(artifact.size for artifact in artifacts) + pending_bytes
        return (policy.max_file_count is not None and file_count > policy.max_file_count) or (
            policy.max_total_bytes is not None and total_bytes > policy.max_total_bytes
        )

    def _smuggle_temp_usage_locked(self) -> SmuggleTempUsage:
        """Return current generated SMUGGLE temp usage."""
        artifacts = self._smuggle_temp_artifacts_locked()
        return SmuggleTempUsage(
            total_bytes=sum(artifact.size for artifact in artifacts),
            file_count=len(artifacts),
        )

    def _smuggle_temp_artifacts_locked(self) -> list[SmuggleTempArtifact]:
        """Return existing generated SMUGGLE temp artifacts."""
        artifacts: list[SmuggleTempArtifact] = []
        for path in self.upload_dir.glob("smuggle_*.html"):
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                stat_result = path.stat()
            except OSError:
                self._temp_smuggle_files.discard(str(path))
                continue
            artifacts.append(
                SmuggleTempArtifact(
                    path=path,
                    size=stat_result.st_size,
                    mtime=stat_result.st_mtime,
                )
            )
        return artifacts

    def _remove_smuggle_temp_artifact_locked(self, path: Path) -> bool:
        """Remove one generated artifact and unregister it."""
        try:
            path.unlink(missing_ok=True)
        except OSError:
            return False
        self._temp_smuggle_files.discard(str(path))
        return True

    def _smuggle_too_large_response(self, source_size: int, source_size_limit: int) -> HTTPResponse:
        """Build a stable JSON 413 response for over-limit SMUGGLE sources."""
        response = HTTPResponse(413)
        response.set_body(
            json.dumps(
                {
                    "error": (
                        f"SMUGGLE source too large. Max size: {self.format_size(source_size_limit)}"
                    ),
                    "status": 413,
                    "file_size": source_size,
                    "file_size_human": self.format_size(source_size),
                    "max_size": source_size_limit,
                    "max_size_human": self.format_size(source_size_limit),
                }
            ),
            "application/json",
        )
        return response

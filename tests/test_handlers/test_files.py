"""Tests for file handler utilities."""

import base64
import json
import threading
from pathlib import Path

from src.handlers import HandlerMixin
from src.http.utils import make_unique_filename, sanitize_filename
from tests.conftest import make_request


class UploadStubServer(HandlerMixin):
    """Minimal concrete class for upload handler tests."""

    def __init__(self, root_dir: Path, upload_dir: Path):
        self.root_dir = root_dir
        self.upload_dir = upload_dir
        self.notes_dir = root_dir / "notes"
        self.notes_dir.mkdir(exist_ok=True)
        self.cors_origin = None
        self.sandbox_mode = False
        self.opsec_mode = False
        self.advanced_upload_enabled = True
        self._temp_smuggle_files: set[str] = set()
        self._smuggle_lock = threading.Lock()
        self._notes_lock = threading.Lock()
        self._ecdh_manager = None
        self.method_handlers = self.build_method_handlers()

    def get_metrics(self):
        return {
            "uptime_seconds": 0,
            "total_requests": 0,
            "total_errors": 0,
            "client_errors": 0,
            "server_errors": 0,
            "bytes_sent": 0,
            "status_counts": {},
        }


def _run_two_uploads(upload):
    """Run two upload calls at once and return their responses."""
    start = threading.Barrier(2)
    results: list[object] = [None, None]
    errors: list[BaseException] = []

    def worker(index: int) -> None:
        try:
            start.wait(timeout=5)
            results[index] = upload(index)
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker, args=(index,)) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert not errors
    assert all(result is not None for result in results)
    return results


def _force_first_two_exists_checks_to_miss(monkeypatch, target: Path) -> None:
    """Make the first two existence checks for *target* observe an absent file."""
    original_exists = Path.exists
    exists_barrier = threading.Barrier(2)
    lock = threading.Lock()
    calls = 0

    def fake_exists(self: Path) -> bool:
        nonlocal calls
        if self == target:
            with lock:
                calls += 1
                should_force_missing = calls <= 2
            if should_force_missing:
                exists_barrier.wait(timeout=5)
                return False
        return original_exists(self)

    monkeypatch.setattr(Path, "exists", fake_exists)


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_simple_filename(self):
        """Test that simple filenames are unchanged."""
        assert sanitize_filename("document.pdf") == "document.pdf"

    def test_removes_path_separators(self):
        """Test removal of path separators."""
        result = sanitize_filename("../../../etc/passwd")
        assert "/" not in result
        assert ".." not in result

    def test_removes_backslashes(self):
        """Test removal of backslashes."""
        result = sanitize_filename("..\\..\\windows\\system32")
        assert "\\" not in result

    def test_replaces_spaces(self):
        """Test handling of spaces in filenames."""
        result = sanitize_filename("file with spaces.txt")
        assert "file" in result.lower()

    def test_empty_filename(self):
        """Test handling of empty filename."""
        result = sanitize_filename("")
        assert len(result) > 0  # Should return some default

    def test_special_characters(self):
        """Test removal of special characters."""
        result = sanitize_filename('file<>:"|?*.txt')
        # Dangerous characters should be removed/replaced
        for char in '<>:"|?*':
            assert char not in result


class TestMakeUniqueFilename:
    """Tests for make_unique_filename function."""

    def test_unique_when_not_exists(self, temp_dir: Path):
        """Test that non-existing filename is returned as-is."""
        file_path = temp_dir / "newfile.txt"

        result = make_unique_filename(file_path)

        assert result == file_path

    def test_adds_suffix_when_exists(self, temp_dir: Path):
        """Test that suffix is added when file exists."""
        file_path = temp_dir / "existing.txt"
        file_path.touch()

        result = make_unique_filename(file_path)

        assert result != file_path
        assert "existing" in result.stem
        assert result.suffix == ".txt"

    def test_increments_suffix(self, temp_dir: Path):
        """Test that suffix increments for multiple collisions."""
        base_path = temp_dir / "file.txt"
        base_path.touch()
        (temp_dir / "file_1.txt").touch()

        result = make_unique_filename(base_path)

        assert result.stem.endswith("_2") or result.stem.endswith("_1") is False

    def test_preserves_extension(self, temp_dir: Path):
        """Test that file extension is preserved."""
        file_path = temp_dir / "document.pdf"
        file_path.touch()

        result = make_unique_filename(file_path)

        assert result.suffix == ".pdf"


class TestExclusiveUploadWrites:
    """Regression coverage for concurrent same-name uploads."""

    def test_standard_upload_reserves_distinct_destination_under_race(
        self,
        temp_dir: Path,
        upload_dir: Path,
        monkeypatch,
    ):
        server = UploadStubServer(temp_dir, upload_dir)
        target = upload_dir / "race.txt"
        _force_first_two_exists_checks_to_miss(monkeypatch, target)
        payloads = [b"first standard payload", b"second standard payload"]

        def upload(index: int):
            return server.handle_none(
                make_request(
                    "POST",
                    "/",
                    headers={"X-File-Name": "race.txt"},
                    body=payloads[index],
                )
            )

        responses = _run_two_uploads(upload)

        assert [response.status_code for response in responses] == [201, 201]
        bodies = [json.loads(response.body) for response in responses]
        filenames = [body["filename"] for body in bodies]
        assert len(set(filenames)) == 2
        assert {body["path"] for body in bodies} == {f"/uploads/{name}" for name in filenames}
        assert {(upload_dir / name).read_bytes() for name in filenames} == set(payloads)

    def test_advanced_upload_reserves_distinct_destination_under_race(
        self,
        temp_dir: Path,
        upload_dir: Path,
        monkeypatch,
    ):
        server = UploadStubServer(temp_dir, upload_dir)
        target = upload_dir / "advanced-race.txt"
        _force_first_two_exists_checks_to_miss(monkeypatch, target)
        payloads = [b"first advanced payload", b"second advanced payload"]

        def upload(index: int):
            body = json.dumps(
                {
                    "d": base64.b64encode(payloads[index]).decode("ascii"),
                    "n": "advanced-race.txt",
                }
            ).encode("ascii")
            return server.handle_advanced_upload(make_request("XUPLOAD", "/", body=body))

        responses = _run_two_uploads(upload)

        assert [response.status_code for response in responses] == [200, 200]
        assert [json.loads(response.body)["ok"] for response in responses] == [True, True]
        saved_files = sorted(path for path in upload_dir.iterdir() if path.is_file())
        assert len(saved_files) == 2
        assert {path.read_bytes() for path in saved_files} == set(payloads)

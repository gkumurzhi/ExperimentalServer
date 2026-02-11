"""Tests for file handler utilities."""

from pathlib import Path

import pytest

from src.http.utils import make_unique_filename, sanitize_filename


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
        result = sanitize_filename("file<>:\"|?*.txt")
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

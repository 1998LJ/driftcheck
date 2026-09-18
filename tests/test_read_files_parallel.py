"""Tests for _read_files_parallel error reporting (issue #178)."""
import warnings
from pathlib import Path
from unittest.mock import patch, MagicMock

from driftcheck.detector import _read_files_parallel, _read_text_safe


def test_read_files_parallel_success(tmp_path):
    """All files readable — no warnings."""
    f1 = tmp_path / "README.md"
    f1.write_text("hello")
    f2 = tmp_path / "setup.py"
    f2.write_text("world")

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = _read_files_parallel(tmp_path, ["*.md", "*.py"])
        assert "hello" in result
        assert "world" in result
        assert len(w) == 0


def test_read_files_parallel_none_files(tmp_path):
    """No matching files — empty string."""
    result = _read_files_parallel(tmp_path, ["*.nonexistent"])
    assert result == ""


def test_read_files_parallel_logs_failures(tmp_path):
    """When _read_text_safe raises, warning is emitted."""
    f1 = tmp_path / "ok.md"
    f1.write_text("ok content")

    original = _read_text_safe

    def fake_safe(path, max_size=1_000_000):
        if "ok" in str(path):
            return original(path, max_size)
        raise OSError("permission denied")

    with patch("driftcheck.detector._read_text_safe", side_effect=fake_safe):
        # Create a second file that will fail
        f2 = tmp_path / "denied.md"
        f2.write_text("no read")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _read_files_parallel(tmp_path, ["*.md"])
            assert "ok content" in result
            assert len(w) == 1
            assert "failed to read" in str(w[0].message)
            assert "permission denied" in str(w[0].message)


def test_read_files_parallel_caps_warning_at_5(tmp_path):
    """Warning message caps at 5 failed files with '...'."""
    files = []
    for i in range(7):
        f = tmp_path / f"file{i}.md"
        f.write_text(f"content {i}")
        files.append(f)

    def fake_safe(path, max_size=1_000_000):
        raise OSError(f"denied for {path.name}")

    with patch("driftcheck.detector._read_text_safe", side_effect=fake_safe):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = _read_files_parallel(tmp_path, ["*.md"])
            assert len(w) == 1
            msg = str(w[0].message)
            assert "7 file(s) failed to read" in msg
            assert "..." in msg  # capped indicator

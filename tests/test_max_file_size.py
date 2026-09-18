"""Tests for _read_text_safe OOM protection (issue #150)."""
from __future__ import annotations
import tempfile
from pathlib import Path
from driftcheck.detector import _read_text_safe


class TestReadTextSafe:
    """Test the _read_text_safe helper for OOM protection."""

    def test_reads_small_file(self, tmp_path):
        """Small files should be read normally."""
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        assert _read_text_safe(f) == "hello world"

    def test_returns_none_for_missing_file(self, tmp_path):
        """Non-existent files should return None."""
        f = tmp_path / "nonexistent.txt"
        assert _read_text_safe(f) is None

    def test_returns_none_for_large_file(self, tmp_path):
        """Files larger than max_size should return None."""
        f = tmp_path / "large.txt"
        f.write_text("x" * 100)
        assert _read_text_safe(f, max_size=50) is None

    def test_accepts_file_at_exact_limit(self, tmp_path):
        """File exactly at the size limit should be read."""
        f = tmp_path / "exact.txt"
        f.write_text("x" * 100)
        assert _read_text_safe(f, max_size=100) == "x" * 100

    def test_returns_none_for_binary_file(self, tmp_path):
        """Binary files (containing null bytes) should return None."""
        f = tmp_path / "binary.bin"
        f.write_bytes(b"\x00\x01\x02\x03")
        assert _read_text_safe(f) is None

    def test_reads_text_file_without_null_bytes(self, tmp_path):
        """Text files without null bytes should be read."""
        f = tmp_path / "text.txt"
        f.write_text("Hello, World!")
        assert _read_text_safe(f) == "Hello, World!"

    def test_default_max_size_is_1mb(self, tmp_path):
        """Default max_size should be 1MB (1_000_000 bytes)."""
        f = tmp_path / "small.txt"
        f.write_text("small content")
        # 1MB = 1_000_000 bytes, small file should pass
        result = _read_text_safe(f)
        assert result == "small content"

    def test_large_file_with_custom_limit(self, tmp_path):
        """Custom max_size limit should work."""
        f = tmp_path / "medium.txt"
        f.write_text("x" * 2000)
        # Over 1KB limit
        assert _read_text_safe(f, max_size=1000) is None
        # Under 10KB limit
        assert _read_text_safe(f, max_size=10000) == "x" * 2000

    def test_handles_permission_error(self, tmp_path):
        """Permission errors should return None gracefully."""
        f = tmp_path / "noperm.txt"
        f.write_text("secret")
        f.chmod(0o000)
        try:
            result = _read_text_safe(f)
            # Either None (permission denied) or "text" (running as root)
            assert result is None or result == "secret"
        finally:
            f.chmod(0o644)


class TestScanRepoMaxFileSize:
    """Test max_file_size integration with scan_repo."""

    def test_config_default_max_file_size(self):
        """Default config should have max_file_size = 1_000_000."""
        from driftcheck.config import load_config
        with tempfile.TemporaryDirectory() as td:
            config = load_config(Path(td))
            assert config["max_file_size"] == 1_000_000

    def test_custom_max_file_size_in_config(self, tmp_path):
        """Custom max_file_size from .driftcheck.toml should be respected."""
        from driftcheck.config import load_config
        config_file = tmp_path / ".driftcheck.toml"
        config_file.write_text("[driftcheck]\nmax_file_size = 500\n")
        config = load_config(tmp_path)
        assert config["max_file_size"] == 500

    def test_large_file_does_not_cause_oom(self, tmp_path):
        """scan_repo should not OOM on large files (issue #150)."""
        from driftcheck.detector import scan_repo
        # Create a large file (2MB) - bigger than default 1MB limit
        large_file = tmp_path / "large.log"
        large_file.write_text("x" * 2_000_000)
        # Should complete without OOM
        result = scan_repo(tmp_path)
        assert isinstance(result, dict)

    def test_binary_file_is_skipped(self, tmp_path):
        """Binary files should be skipped automatically."""
        from driftcheck.detector import scan_repo
        # Create a binary file
        binary = tmp_path / "image.bin"
        binary.write_bytes(b"\x00\x01\x02\x03" * 100)
        # Should complete without errors
        result = scan_repo(tmp_path)
        assert isinstance(result, dict)


class TestCliMaxFileSize:
    """Test --max-file-size CLI flag."""

    def test_max_file_size_flag_parsed(self):
        """--max-file-size flag should be parseable."""
        from driftcheck.cli import main
        with tempfile.TemporaryDirectory() as td:
            # Just test parsing, will return 0 (no drifts)
            result = main(["--max-file-size", "500", td])
            assert result in (0, 1)

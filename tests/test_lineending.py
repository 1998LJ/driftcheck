"""Tests for Lineending drift detector."""
from pathlib import Path

import pytest

from driftcheck.detectors.lineending import find_lineending_drift


class TestFindLineendingDrift:
    def test_missing_gitattributes(self, tmp_path):
        (tmp_path / "main.py").write_text("print('hello')\n")
        result = find_lineending_drift(tmp_path)
        assert len(result) == 1
        assert result[0]["kind"] == "lineending"
        assert "missing" in result[0]["detail"]

    def test_present_gitattributes(self, tmp_path):
        (tmp_path / "main.py").write_text("print('hello')\n", newline="\n")
        (tmp_path / ".gitattributes").write_text("* text=auto eol=lf\n", newline="\n")
        result = find_lineending_drift(tmp_path)
        assert result == []

    def test_incomplete_gitattributes(self, tmp_path):
        (tmp_path / "main.py").write_text("print('hello')\n")
        (tmp_path / ".gitattributes").write_text("# just a comment\n")
        result = find_lineending_drift(tmp_path)
        assert len(result) == 1
        assert "does not set" in result[0]["detail"]

    def test_no_source_files(self, tmp_path):
        result = find_lineending_drift(tmp_path)
        assert result == []

    def test_lineending_drift_detected(self, tmp_path):
        """Verifies that files with CRLF line endings are flagged when policy is LF."""
        (tmp_path / ".gitattributes").write_text("* text=auto eol=lf\n")
        (tmp_path / "main.py").write_bytes(b"print('hello')\r\n")
        result = find_lineending_drift(tmp_path)
        assert len(result) == 1
        assert result[0]["file"] == "main.py"
        assert result[0]["type"] == "lineending_drift"
        assert result[0]["kind"] == "lineending"
        assert result[0]["expected"] == "LF"
        assert result[0]["found"] == "CRLF"
        assert "CRLF" in result[0]["detail"]

    def test_lineending_drift_clean(self, tmp_path):
        """Verifies that LF-only files produce no drift."""
        (tmp_path / ".gitattributes").write_text("* text=auto eol=lf\n")
        (tmp_path / "main.py").write_bytes(b"print('hello')\n")
        (tmp_path / "app.js").write_bytes(b"console.log('hi');\n")
        result = find_lineending_drift(tmp_path)
        assert result == []

    def test_lineending_drift_respects_gitattributes_override(self, tmp_path):
        """Files matching explicit eol=crlf in .gitattributes are not flagged."""
        (tmp_path / ".gitattributes").write_text("* text=auto eol=lf\n*.bat text eol=crlf\n")
        (tmp_path / "run.bat").write_bytes(b"@echo off\r\n")
        (tmp_path / "main.py").write_bytes(b"print('hello')\n")
        result = find_lineending_drift(tmp_path)
        assert result == []

    def test_lineending_drift_skips_vendor_and_git_dirs(self, tmp_path):
        """Vendor and git directories are skipped during CRLF scanning."""
        (tmp_path / ".gitattributes").write_text("* text=auto eol=lf\n")
        vendor = tmp_path / "node_modules" / "pkg"
        vendor.mkdir(parents=True)
        (vendor / "index.js").write_bytes(b"module.exports = {};\r\n")
        (tmp_path / "main.py").write_bytes(b"print('hello')\n")
        result = find_lineending_drift(tmp_path)
        assert result == []

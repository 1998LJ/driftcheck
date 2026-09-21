"""Tests for driftcheck --explain command (issue #271)."""
from pathlib import Path
import json
import sys
import pytest
from driftcheck.explain import Explainer


def test_explain_returns_full_context(tmp_path):
    """Explain should return drift type, file, line, actual, expected, diff, impact, fix."""
    # Create a fake repo with README that has a stale Rust version
    (tmp_path / "rust-toolchain.toml").write_text('[toolchain]\nchannel = "1.96.1"\n')
    (tmp_path / "README.md").write_text("# My Project\n\nRequires Rust 1.93.0 or later.\n")

    explainer = Explainer(tmp_path)
    drift = {
        "file": "README.md",
        "doc_version": "1.93.0",
        "toolchain_version": "1.96.1",
    }
    result = explainer.explain(drift, "rust_drifts")

    assert result["drift"] == "rust_drifts"
    assert result["file"] == "README.md"
    assert result["line"] == 3  # line with "1.93.0"
    assert result["actual"] == "1.93.0"
    assert result["expected"] == "1.96.1"
    assert "- 1.93.0" in result["diff"]
    assert "+ 1.96.1" in result["diff"]
    assert "Rust" in result["impact"] or "compile" in result["impact"]
    assert "1.93.0" in result["fix"]
    assert "1.96.1" in result["fix"]


def test_explain_text_format(tmp_path):
    """explain_text should return human-readable multi-line string."""
    (tmp_path / "README.md").write_text("# Project\n\nNode 18.0.0\n")

    explainer = Explainer(tmp_path)
    drift = {
        "file": "README.md",
        "doc_version": "18.0.0",
        "package_version": "20.0.0",
    }
    text = explainer.explain_text(drift, "node_drifts")

    assert "Drift: node_drifts" in text
    assert "File: README.md" in text
    assert "Actual: 18.0.0" in text
    assert "Expected: 20.0.0" in text


def test_explain_json_format(tmp_path):
    """explain_json should return a dict (JSON-serializable)."""
    (tmp_path / "README.md").write_text("# Project\n\nGo 1.20\n")

    explainer = Explainer(tmp_path)
    drift = {
        "file": "README.md",
        "doc_version": "1.20",
        "gomod_version": "1.22",
    }
    result = explainer.explain_json(drift, "go_drifts")

    assert isinstance(result, dict)
    assert result["drift"] == "go_drifts"
    assert result["file"] == "README.md"
    assert result["actual"] == "1.20"
    assert result["expected"] == "1.22"


def test_explain_all_gathers_all_drifts(tmp_path):
    """explain_all should explain every drift in scan results."""
    (tmp_path / "README.md").write_text("# Project\n\nRust 1.93.0\nNode 18.0.0\n")

    explainer = Explainer(tmp_path)
    results = {
        "rust_drifts": [{"file": "README.md", "doc_version": "1.93.0", "toolchain_version": "1.96.1"}],
        "node_drifts": [{"file": "README.md", "doc_version": "18.0.0", "package_version": "20.0.0"}],
    }
    all_exp = explainer.explain_all(results)

    assert len(all_exp) == 2
    types = {e["drift"] for e in all_exp}
    assert types == {"rust_drifts", "node_drifts"}


def test_explain_fix_updates_file(tmp_path):
    """explain_fix should update docs file (not toolchain files)."""
    (tmp_path / "rust-toolchain.toml").write_text('[toolchain]\nchannel = "1.96.1"\n')
    (tmp_path / "README.md").write_text("# Project\n\nRust 1.93.0\n")

    explainer = Explainer(tmp_path)
    drift = {
        "file": "README.md",
        "doc_version": "1.93.0",
        "toolchain_version": "1.96.1",
    }
    result = explainer.explain_fix(drift, "rust_drifts")

    assert result == "README.md"
    content = (tmp_path / "README.md").read_text()
    assert "1.96.1" in content
    assert "1.93.0" not in content


def test_explain_fix_skips_toolchain_files(tmp_path):
    """explain_fix should NOT modify toolchain/manifest files."""
    (tmp_path / "rust-toolchain.toml").write_text('[toolchain]\nchannel = "1.96.1"\n')
    (tmp_path / "README.md").write_text("# Project\n\nRust 1.93.0\n")

    explainer = Explainer(tmp_path)
    drift = {
        "file": "rust-toolchain.toml",
        "doc_version": "1.96.1",
    }
    result = explainer.explain_fix(drift, "rust_drifts")

    assert result is None


def test_explain_fix_missing_file(tmp_path):
    """explain_fix returns None when file doesn't exist."""
    explainer = Explainer(tmp_path)
    drift = {
        "file": "NONEXISTENT.md",
        "doc_version": "1.0",
    }
    result = explainer.explain_fix(drift, "rust_drifts")
    assert result is None


def test_explain_impact_description_for_known_drift_types():
    """Each drift type should have a meaningful impact description."""
    from driftcheck.explain import IMPACT_DESCRIPTIONS

    assert "rust_drifts" in IMPACT_DESCRIPTIONS
    assert "node_drifts" in IMPACT_DESCRIPTIONS
    assert "python_drifts" in IMPACT_DESCRIPTIONS
    assert "go_drifts" in IMPACT_DESCRIPTIONS
    # Impact should not be empty
    for key, desc in IMPACT_DESCRIPTIONS.items():
        assert len(desc) > 20, f"Impact description for {key} is too short: {desc!r}"


def test_cli_explain_flag(tmp_path, monkeypatch):
    """CLI --explain should print explanation for a drift."""
    # Create test repo
    (tmp_path / "rust-toolchain.toml").write_text('[toolchain]\nchannel = "1.96.1"\n')
    (tmp_path / "README.md").write_text("# Project\n\nRust 1.93.0\n")

    from driftcheck.cli import main

    monkeypatch.chdir(tmp_path)
    exit_code = main(["--explain", "rust_drifts:README.md", "--explain-format", "text"])
    assert exit_code == 0


def test_cli_explain_all(tmp_path, monkeypatch):
    """CLI --explain-all should print all drifts."""
    (tmp_path / "rust-toolchain.toml").write_text('[toolchain]\nchannel = "1.96.1"\n')
    (tmp_path / "README.md").write_text("# Project\n\nRust 1.93.0\n")

    from driftcheck.cli import main

    monkeypatch.chdir(tmp_path)
    exit_code = main(["--explain-all"])
    assert exit_code == 0


def test_cli_explain_json_format(tmp_path, monkeypatch, capsys):
    """CLI --explain --explain-format json should output valid JSON."""
    (tmp_path / "rust-toolchain.toml").write_text('[toolchain]\nchannel = "1.96.1"\n')
    (tmp_path / "README.md").write_text("# Project\n\nRust 1.93.0\n")

    from driftcheck.cli import main

    monkeypatch.chdir(tmp_path)
    exit_code = main(["--explain", "rust_drifts:README.md", "--explain-format", "json"])
    assert exit_code == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["drift"] == "rust_drifts"
    assert data["actual"] == "1.93.0"
    assert data["expected"] == "1.96.1"


def test_cli_explain_fix(tmp_path, monkeypatch, capsys):
    """CLI --explain --explain-fix should apply the fix."""
    (tmp_path / "rust-toolchain.toml").write_text('[toolchain]\nchannel = "1.96.1"\n')
    (tmp_path / "README.md").write_text("# Project\n\nRust 1.93.0\n")

    from driftcheck.cli import main

    monkeypatch.chdir(tmp_path)
    exit_code = main(["--explain", "rust_drifts:README.md", "--explain-fix"])
    assert exit_code == 0

    content = (tmp_path / "README.md").read_text()
    assert "1.96.1" in content

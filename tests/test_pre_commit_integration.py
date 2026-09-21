"""Tests for driftcheck pre-commit integration."""
import driftcheck.cli as cli


def test_pre_commit_command_outputs_hook(capsys):
    assert cli.main(["pre-commit"]) == 0
    out = capsys.readouterr().out
    assert "- id: driftcheck" in out
    assert "entry: driftcheck --changed-only" in out
    assert "pass_filenames: false" in out


def test_changed_only_filters_to_staged_files(monkeypatch, tmp_path):
    captured = {}

    monkeypatch.setattr(cli, "get_staged_files", lambda root: {"package.json"})

    def fake_scan(root, enabled_detectors=None, max_file_size=None):
        captured["root"] = root
        captured["enabled_detectors"] = enabled_detectors
        return {}

    monkeypatch.setattr(cli, "scan_repo", fake_scan)

    assert cli.main([str(tmp_path), "--changed-only", "--quiet"]) == 0
    assert "node_drifts" in captured["enabled_detectors"]
    assert "bun_drifts" in captured["enabled_detectors"]
    assert "rust_drifts" not in captured["enabled_detectors"]


def test_changed_only_no_staged_files_exits_cleanly(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "get_staged_files", lambda root: set())
    assert cli.main([str(tmp_path), "--changed-only", "--quiet"]) == 0

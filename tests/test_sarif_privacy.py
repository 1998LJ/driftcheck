"""Tests for SARIF output privacy (issue #133): paths should be relative by default."""

from pathlib import Path
from driftcheck.sarif import to_sarif


def _empty_result():
    return {
        "rust_drifts": [],
        "node_drifts": [],
        "python_drifts": [],
        "go_drifts": [],
        "count_drifts": [],
        "actions_drifts": [],
        "lineending_drifts": [],
        "docker_drifts": [],
        "java_drifts": [],
        "maven_drifts": [],
        "terraform_drifts": [],
        "circleci_drifts": [],
        "gitlab_drifts": [],
        "gh_actions_version_drifts": [],
        "k8s_drifts": [],
        "helm_drifts": [],
        "dc_drifts": [],
        "ci_os_drifts": [],
        "dotnet_drifts": [],
        "ruby_drifts": [],
        "php_drifts": [],
        "external_resource_drifts": [],
        "dependabot_drifts": [],
        "lockfile_drifts": [],
    }


def test_sarif_paths_relative_by_default():
    """SARIF output should use repo-relative paths by default."""
    result = _empty_result()
    result["rust_drifts"] = [
        {"file": "README.md", "doc_version": "1.93.0", "toolchain_version": "1.96.1", "pos": 10}
    ]
    root = Path("/home/testuser/myproject")
    doc = to_sarif(result, version="0.1.45", root=root)
    uri = doc["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
    assert "/" not in uri or not uri.startswith("/"), f"Path should be relative, got: {uri}"
    assert ".." not in uri, f"Path should not traverse upward, got: {uri}"


def test_sarif_no_absolute_paths_in_output():
    """SARIF output must never contain /home/ or C:\\Users\\ paths."""
    result = _empty_result()
    result["rust_drifts"] = [
        {"file": "README.md", "doc_version": "1.93.0", "toolchain_version": "1.96.1", "pos": 10}
    ]
    result["_skipped_symlinks"] = [
        "Symlink 'secret' skipped (outside repo root)"
    ]
    root = Path("/home/testuser/myproject")
    doc = to_sarif(result, version="0.1.45", root=root)
    import json
    sarif_str = json.dumps(doc)
    assert "/home/" not in sarif_str, "SARIF output should not contain absolute /home/ paths"


def test_sarif_absolute_paths_flag():
    """With root=None, absolute paths are preserved (for local debugging)."""
    result = _empty_result()
    result["rust_drifts"] = [
        {"file": "/home/testuser/myproject/README.md", "doc_version": "1.93.0", "toolchain_version": "1.96.1", "pos": 10}
    ]
    doc = to_sarif(result, version="0.1.45", root=None)
    uri = doc["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
    assert "/home/" in uri, f"With root=None, absolute paths preserved, got: {uri}"


def test_sarif_skipped_symlinks_no_absolute_target():
    """Skipped symlink messages should never contain the target path."""
    result = _empty_result()
    result["_skipped_symlinks"] = [
        "Symlink 'secret' skipped (outside repo root)"
    ]
    doc = to_sarif(result, version="0.1.45")
    messages = [r["message"]["text"] for r in doc["runs"][0]["results"]]
    for msg in messages:
        assert "/etc/" not in msg
        assert "/home/" not in msg
        assert "C:\\Users\\" not in msg


def test_sarif_paths_no_username_leak():
    """SARIF output should not leak usernames in paths."""
    result = _empty_result()
    result["rust_drifts"] = [
        {"file": "src/main.rs", "doc_version": "1.93.0", "toolchain_version": "1.96.1", "pos": 10}
    ]
    root = Path("/home/johndoe/driftcheck")
    doc = to_sarif(result, version="0.1.45", root=root)
    import json
    sarif_str = json.dumps(doc)
    assert "johndoe" not in sarif_str, "SARIF output should not contain usernames"

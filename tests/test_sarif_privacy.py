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


def test_sarif_repo_root_is_confined_to_uri_base_id():
    """Absolute repo root belongs only in originalUriBaseIds, not result URIs."""
    result = _empty_result()
    result["rust_drifts"] = [
        {"file": "README.md", "doc_version": "1.93.0", "toolchain_version": "1.96.1", "pos": 10}
    ]
    root = Path("/home/testuser/myproject")
    doc = to_sarif(result, version="0.1.45", root=root)

    run = doc["runs"][0]
    base = run["originalUriBaseIds"]["repoRoot"]
    assert base["uri"] == "file:///home/testuser/myproject/"

    artifact = run["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]
    assert artifact == {"uri": "README.md", "uriBaseId": "repoRoot"}


def test_sarif_absolute_paths_flag():
    """With root=None, absolute paths are preserved (for local debugging)."""
    result = _empty_result()
    result["rust_drifts"] = [
        {"file": "/home/testuser/myproject/README.md", "doc_version": "1.93.0", "toolchain_version": "1.96.1", "pos": 10}
    ]
    doc = to_sarif(result, version="0.1.45", root=None)
    run = doc["runs"][0]
    uri = run["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
    assert "/home/" in uri, f"With root=None, absolute paths preserved, got: {uri}"
    assert "originalUriBaseIds" not in run
    assert "uriBaseId" not in run["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]


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


def test_sarif_result_paths_do_not_leak_username():
    """Result artifact URIs stay repo-relative even when the base URI is absolute."""
    result = _empty_result()
    result["rust_drifts"] = [
        {"file": "src/main.rs", "doc_version": "1.93.0", "toolchain_version": "1.96.1", "pos": 10}
    ]
    root = Path("/home/johndoe/driftcheck")
    doc = to_sarif(result, version="0.1.45", root=root)
    artifact = doc["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]
    assert artifact["uri"] == "src/main.rs"
    assert "johndoe" not in artifact["uri"]
    assert artifact["uriBaseId"] == "repoRoot"

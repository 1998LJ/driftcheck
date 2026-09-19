"""Tests for SARIF originalUriBaseIds support (issue #193)."""
import json
from pathlib import Path

from driftcheck.sarif import to_sarif


def _empty_result():
    """Return a result dict with all drift keys set to empty lists."""
    return {
        "toolchain_version": "1.96.1",
        "rust_drifts": [],
        "node_drifts": [],
        "bun_drifts": [],
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


def test_sarif_original_uri_base_ids_present_with_root():
    """When root is provided, originalUriBaseIds must be present."""
    result = _empty_result()
    result["rust_drifts"] = [{"file": "README.md", "doc_version": "1.93.0", "toolchain_version": "1.96.1", "pos": 10}]
    root = Path("/tmp/test-repo")
    doc = to_sarif(result, version="0.1.40", root=root)
    run = doc["runs"][0]
    assert "originalUriBaseIds" in run
    assert "repoRoot" in run["originalUriBaseIds"]
    repo_root = run["originalUriBaseIds"]["repoRoot"]

    assert "description" in repo_root


def test_sarif_original_uri_base_ids_absent_without_root():
    """When root is None (absolute_paths mode), originalUriBaseIds must be absent."""
    result = _empty_result()
    result["rust_drifts"] = [{"file": "README.md", "doc_version": "1.93.0", "toolchain_version": "1.96.1", "pos": 10}]
    doc = to_sarif(result, version="0.1.40", root=None)
    run = doc["runs"][0]
    assert "originalUriBaseIds" not in run


def test_sarif_uses_repo_root_prefix():
    """File URIs must use {repoRoot}/ prefix when root is set."""
    result = _empty_result()
    result["rust_drifts"] = [{"file": "README.md", "doc_version": "1.93.0", "toolchain_version": "1.96.1", "pos": 10}]
    root = Path("/tmp/test-repo")
    doc = to_sarif(result, version="0.1.40", root=root)
    run = doc["runs"][0]
    uri = run["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
    assert uri.startswith("{repoRoot}/")
    assert "{repoRoot}/README.md" == uri


def test_sarif_nested_path_uses_repo_root_prefix():
    """Nested paths must use {repoRoot}/ prefix."""
    result = _empty_result()
    result["rust_drifts"] = [{"file": "src/lib.rs", "doc_version": "1.93.0", "toolchain_version": "1.96.1", "pos": 10}]
    root = Path("/tmp/test-repo")
    doc = to_sarif(result, version="0.1.40", root=root)
    run = doc["runs"][0]
    uri = run["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
    assert uri == "{repoRoot}/src/lib.rs"


def test_sarif_no_drift_still_has_original_uri_base_ids():
    """Even with no drift, originalUriBaseIds should be present if root is set."""
    result = _empty_result()
    root = Path("/tmp/test-repo")
    doc = to_sarif(result, version="0.1.40", root=root)
    run = doc["runs"][0]
    assert "originalUriBaseIds" in run
    assert run["results"] == []



"""Tests for package.json/package-lock.json integrity drift detection."""
from __future__ import annotations

import json
import os
import time

from driftcheck.detector import scan_repo
from driftcheck.sarif import to_sarif
from driftcheck.detectors.package_lock import (
    find_package_lock_drift,
    satisfies_npm_range,
)


def _write_package(tmp_path, dependencies=None):
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "demo", "dependencies": dependencies or {}}),
        encoding="utf-8",
    )


def _write_lock(tmp_path, packages, lockfile_version=3):
    data = {
        "name": "demo",
        "lockfileVersion": lockfile_version,
        "packages": {"": {"name": "demo"}, **{
            f"node_modules/{name}": {"version": version}
            for name, version in packages.items()
        }},
    }
    (tmp_path / "package-lock.json").write_text(json.dumps(data), encoding="utf-8")


def test_semver_common_npm_ranges():
    assert satisfies_npm_range("1.5.0", "^1.2.3") is True
    assert satisfies_npm_range("2.0.0", "^1.2.3") is False
    assert satisfies_npm_range("1.2.9", "~1.2.3") is True
    assert satisfies_npm_range("1.3.0", "~1.2.3") is False
    assert satisfies_npm_range("1.5.0", ">=1.2.0 <2.0.0") is True
    assert satisfies_npm_range("2.1.0", "1.x || >=3.0.0") is False
    assert satisfies_npm_range("3.1.0", "1.x || >=3.0.0") is True


def test_exact_and_range_match_have_no_drift(tmp_path):
    _write_package(tmp_path, {"alpha": "1.2.3", "beta": "^2.0.0"})
    _write_lock(tmp_path, {"alpha": "1.2.3", "beta": "2.4.1"})
    assert [
        d for d in find_package_lock_drift(tmp_path)
        if d["kind"] in {"lockfile_range_violation", "lockfile_dependency_missing"}
    ] == []


def test_range_violation_is_reported(tmp_path):
    _write_package(tmp_path, {"alpha": "^1.2.3"})
    _write_lock(tmp_path, {"alpha": "2.0.0"})

    drifts = find_package_lock_drift(tmp_path)
    violations = [d for d in drifts if d["kind"] == "lockfile_range_violation"]
    assert len(violations) == 1
    assert violations[0]["dependency"] == "alpha"
    assert violations[0]["declared"] == "^1.2.3"
    assert violations[0]["resolved"] == "2.0.0"


def test_dependency_missing_from_lockfile_is_reported(tmp_path):
    _write_package(tmp_path, {"alpha": "^1.0.0"})
    _write_lock(tmp_path, {})

    drifts = find_package_lock_drift(tmp_path)
    missing = [d for d in drifts if d["kind"] == "lockfile_dependency_missing"]
    assert len(missing) == 1
    assert missing[0]["dependency"] == "alpha"


def test_missing_package_lock_is_reported(tmp_path):
    _write_package(tmp_path, {"alpha": "^1.0.0"})
    drifts = find_package_lock_drift(tmp_path)
    assert len(drifts) == 1
    assert drifts[0]["kind"] == "lockfile_missing"


def test_alternative_node_lockfile_avoids_package_lock_missing(tmp_path):
    _write_package(tmp_path, {"alpha": "^1.0.0"})
    (tmp_path / "yarn.lock").write_text("# yarn lockfile", encoding="utf-8")
    assert find_package_lock_drift(tmp_path) == []


def test_stale_package_lock_is_reported(tmp_path):
    _write_package(tmp_path, {"alpha": "^1.0.0"})
    _write_lock(tmp_path, {"alpha": "1.2.0"})
    lock_path = tmp_path / "package-lock.json"
    package_path = tmp_path / "package.json"
    past = time.time() - 3600
    os.utime(lock_path, (past, past))
    os.utime(package_path, None)

    drifts = find_package_lock_drift(tmp_path)
    assert any(d["kind"] == "lockfile_stale" for d in drifts)


def test_lockfile_v2_packages_are_supported(tmp_path):
    _write_package(tmp_path, {"alpha": "^1.0.0"})
    _write_lock(tmp_path, {"alpha": "1.9.0"}, lockfile_version=2)
    assert not any(
        d["kind"] == "lockfile_range_violation"
        for d in find_package_lock_drift(tmp_path)
    )


def test_lockfile_v1_dependencies_are_supported(tmp_path):
    _write_package(tmp_path, {"alpha": "~1.2.0"})
    (tmp_path / "package-lock.json").write_text(
        json.dumps({
            "lockfileVersion": 1,
            "dependencies": {"alpha": {"version": "1.2.8"}},
        }),
        encoding="utf-8",
    )
    assert not any(
        d["kind"] == "lockfile_range_violation"
        for d in find_package_lock_drift(tmp_path)
    )


def test_non_semver_dependency_sources_are_skipped(tmp_path):
    _write_package(tmp_path, {"alpha": "git+https://example.com/alpha.git"})
    _write_lock(tmp_path, {"alpha": "9.9.9"})
    assert not any(
        d["kind"] == "lockfile_range_violation"
        for d in find_package_lock_drift(tmp_path)
    )


def test_scan_repo_exposes_blocking_package_lock_integrity(tmp_path):
    _write_package(tmp_path, {"alpha": "^1.0.0"})
    _write_lock(tmp_path, {"alpha": "2.0.0"})

    result = scan_repo(tmp_path)
    assert len(result["package_lock_drifts"]) == 1
    assert result["package_lock_drifts"][0]["kind"] == "lockfile_range_violation"


def test_sarif_includes_package_lock_integrity_rule():
    result = {
        "package_lock_drifts": [{
            "file": "package-lock.json",
            "kind": "lockfile_range_violation",
            "dependency": "alpha",
            "declared": "^1.0.0",
            "resolved": "2.0.0",
            "detail": "alpha@2.0.0 does not satisfy package.json range ^1.0.0",
            "pos": 0,
        }]
    }
    sarif = to_sarif(result, version="test")
    run = sarif["runs"][0]
    assert any(
        rule["id"] == "package-lock-integrity-drift"
        for rule in run["tool"]["driver"]["rules"]
    )
    finding = next(
        item for item in run["results"]
        if item["ruleId"] == "package-lock-integrity-drift"
    )
    assert finding["level"] == "error"

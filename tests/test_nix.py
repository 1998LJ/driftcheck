"""Tests for Nix flake.lock drift detection."""

from __future__ import annotations

import json
from pathlib import Path

from driftcheck.detectors.nix import find_nix_drift, _parse_flake_lock


def _write_flake_lock(root: Path, nodes: dict) -> None:
    """Write a minimal flake.lock with the given nodes."""
    flake = {"nodes": nodes, "root": "root", "version": 7}
    (root / "flake.lock").write_text(json.dumps(flake), encoding="utf-8")


def _write_readme(root: Path, content: str) -> None:
    (root / "README.md").write_text(content, encoding="utf-8")


def test_parse_flake_lock_basic(tmp_path: Path) -> None:
    """Parse flake.lock and extract nixpkgs version."""
    nodes = {
        "nixpkgs": {
            "locked": {
                "lastModified": 1700000000,
                "narHash": "sha256-abc123",
                "owner": "NixOS",
                "repo": "nixpkgs",
                "rev": "abc123",
                "type": "github",
                "version": "24.05",
            }
        },
        "root": {
            "inputs": {"nixpkgs": "nixpkgs"},
        },
    }
    _write_flake_lock(tmp_path, nodes)
    result = _parse_flake_lock((tmp_path / "flake.lock").read_text())
    assert result == {"nixpkgs": "24.05"}


def test_parse_flake_lock_unstable(tmp_path: Path) -> None:
    """Parse flake.lock with nixpkgs-unstable."""
    nodes = {
        "nixpkgs-unstable": {
            "locked": {
                "lastModified": 1700000000,
                "narHash": "sha256-abc123",
                "owner": "NixOS",
                "repo": "nixpkgs",
                "rev": "abc123",
                "type": "github",
            }
        },
    }
    _write_flake_lock(tmp_path, nodes)
    result = _parse_flake_lock((tmp_path / "flake.lock").read_text())
    # Should have rev- prefix since no version
    assert "nixpkgs-unstable" in result


def test_no_drift_when_versions_match(tmp_path: Path) -> None:
    """No drift when README matches flake.lock."""
    nodes = {
        "nixpkgs": {
            "locked": {
                "lastModified": 1700000000,
                "narHash": "sha256-abc123",
                "owner": "NixOS",
                "repo": "nixpkgs",
                "rev": "abc123",
                "type": "github",
                "version": "24.05",
            }
        },
    }
    _write_flake_lock(tmp_path, nodes)
    _write_readme(tmp_path, "This project uses nixpkgs 24.05 for reproducible builds.")
    drifts = find_nix_drift(tmp_path)
    assert drifts == []


def test_drift_when_versions_mismatch(tmp_path: Path) -> None:
    """Drift detected when README version differs from flake.lock."""
    nodes = {
        "nixpkgs": {
            "locked": {
                "lastModified": 1700000000,
                "narHash": "sha256-abc123",
                "owner": "NixOS",
                "repo": "nixpkgs",
                "rev": "abc123",
                "type": "github",
                "version": "24.05",
            }
        },
    }
    _write_flake_lock(tmp_path, nodes)
    _write_readme(tmp_path, "This project uses nixpkgs 23.11 for reproducible builds.")
    drifts = find_nix_drift(tmp_path)
    assert len(drifts) == 1
    assert drifts[0]["doc_version"] == "23.11"
    assert drifts[0]["config_version"] == "24.05"
    assert drifts[0]["tool"] == "nixpkgs"


def test_no_flake_lock_returns_empty(tmp_path: Path) -> None:
    """No drift when flake.lock doesn't exist."""
    _write_readme(tmp_path, "This project uses nixpkgs 24.05.")
    drifts = find_nix_drift(tmp_path)
    assert drifts == []


def test_no_readme_returns_empty(tmp_path: Path) -> None:
    """No drift when README doesn't exist."""
    nodes = {
        "nixpkgs": {
            "locked": {
                "lastModified": 1700000000,
                "narHash": "sha256-abc123",
                "owner": "NixOS",
                "repo": "nixpkgs",
                "rev": "abc123",
                "type": "github",
                "version": "24.05",
            }
        },
    }
    _write_flake_lock(tmp_path, nodes)
    drifts = find_nix_drift(tmp_path)
    assert drifts == []


def test_nixos_prefix_matching(tmp_path: Path) -> None:
    """Match nixos- prefix in README."""
    nodes = {
        "nixpkgs": {
            "locked": {
                "lastModified": 1700000000,
                "narHash": "sha256-abc123",
                "owner": "NixOS",
                "repo": "nixpkgs",
                "rev": "abc123",
                "type": "github",
                "version": "24.05",
            }
        },
    }
    _write_flake_lock(tmp_path, nodes)
    _write_readme(tmp_path, "Built with nixos-24.05.")
    drifts = find_nix_drift(tmp_path)
    assert len(drifts) == 0  # Should match


def test_multiple_nixpkgs_inputs(tmp_path: Path) -> None:
    """Handle multiple nixpkgs inputs (stable + unstable)."""
    nodes = {
        "nixpkgs": {
            "locked": {
                "lastModified": 1700000000,
                "narHash": "sha256-abc123",
                "owner": "NixOS",
                "repo": "nixpkgs",
                "rev": "abc123",
                "type": "github",
                "version": "24.05",
            }
        },
        "nixpkgs-unstable": {
            "locked": {
                "lastModified": 1700000000,
                "narHash": "sha256-def456",
                "owner": "NixOS",
                "repo": "nixpkgs",
                "rev": "def456",
                "type": "github",
            }
        },
    }
    _write_flake_lock(tmp_path, nodes)
    _write_readme(tmp_path, "Uses nixpkgs 24.05 and nixpkgs-unstable.")
    drifts = find_nix_drift(tmp_path)
    # nixpkgs 24.05 matches (stable vs stable), nixpkgs-unstable vs rev-1700000000 (unstable vs unstable)
    # Only 1 drift: nixpkgs-unstable "unstable" != "rev-1700000000"
    assert len(drifts) == 1
    assert drifts[0]["tool"] == "nixpkgs-unstable"
    assert drifts[0]["doc_version"] == "unstable"


def test_invalid_json_returns_empty(tmp_path: Path) -> None:
    """Invalid JSON in flake.lock returns empty dict."""
    (tmp_path / "flake.lock").write_text("not json", encoding="utf-8")
    result = _parse_flake_lock("not json")
    assert result == {}

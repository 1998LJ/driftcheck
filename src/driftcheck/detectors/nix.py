"""Nix flake.lock drift detection."""

from __future__ import annotations

import json
import re
from pathlib import Path

# Match nixpkgs version mentions in README: "nixpkgs 24.05", "nixos-24.05", "nixpkgs-unstable"
NIXPKGS_RE = re.compile(
    r"\b(?:nixpkgs|nixos)[-_ ]?(?P<version>\d+\.\d+(?:-\w+)?|unstable)\b",
    re.IGNORECASE,
)

# Match flake input names that map to nixpkgs
NIXPKGS_NAMES = {"nixpkgs", "nixos", "nixpkgs-unstable", "nixpkgs-stable"}


def _docs(root: Path) -> dict[str, str]:
    path = root / "README.md"
    return (
        {"README.md": path.read_text(encoding="utf-8", errors="replace")}
        if path.exists()
        else {}
    )


def _parse_flake_lock(text: str) -> dict[str, str]:
    """Parse flake.lock and return {input_name: version} for nixpkgs-related inputs."""
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {}

    nodes = data.get("nodes", {})
    result: dict[str, str] = {}

    for name, node in nodes.items():
        if name not in NIXPKGS_NAMES:
            continue
        locked = node.get("locked", {})
        version = locked.get("version")
        if version:
            result[name] = version
        elif locked.get("rev"):
            # Use lastModified as a proxy for version when only rev is available
            last_mod = locked.get("lastModified", "")
            if last_mod:
                result[name] = f"rev-{last_mod}"

    return result


def _doc_nixpkgs_versions(content: str) -> list[tuple[str, int]]:
    """Find all nixpkgs version mentions in README content."""
    return [(m.group("version"), m.start()) for m in NIXPKGS_RE.finditer(content)]


def find_nix_drift(root: Path) -> list[dict]:
    """Detect drift between flake.lock nixpkgs pins and README mentions.

    Returns list of {file, tool, doc_version, config_version, source, pos}.
    """
    docs = _docs(root)
    if not docs:
        return []

    flake_path = root / "flake.lock"
    if not flake_path.exists():
        return []

    flake_text = flake_path.read_text(encoding="utf-8", errors="replace")
    locked = _parse_flake_lock(flake_text)
    if not locked:
        return []

    drifts: list[dict] = []

    for filename, content in docs.items():
        doc_versions = _doc_nixpkgs_versions(content)
        if not doc_versions:
            continue

        for doc_ver, pos in doc_versions:
            # Check against all locked nixpkgs inputs
            for input_name, locked_ver in locked.items():
                # Normalize: "24.05" vs "24.05" or "nixpkgs-unstable" vs "unstable"
                normalized_doc = doc_ver.lower().replace("nixpkgs-", "").replace("nixos-", "")
                normalized_locked = locked_ver.lower().replace("nixpkgs-", "").replace("nixos-", "")

                # Skip comparison between stable and unstable — they are different channels
                doc_is_unstable = normalized_doc == "unstable"
                locked_is_unstable = normalized_locked == "unstable" or normalized_locked.startswith("rev-")
                if doc_is_unstable != locked_is_unstable:
                    continue

                if normalized_doc != normalized_locked:
                    drifts.append(
                        {
                            "file": filename,
                            "tool": input_name,
                            "doc_version": doc_ver,
                            "config_version": locked_ver,
                            "source": "flake.lock",
                            "pos": pos,
                        }
                    )

    return drifts

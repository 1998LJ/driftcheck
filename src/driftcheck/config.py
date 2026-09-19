"""Configuration loading for driftcheck.

Reads .driftcheck.toml from repo root to customize detection behavior.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path
from typing import Any

# All drift type keys — shared across CLI modes
DRIFT_KEYS = [
    "rust_drifts", "node_drifts", "bun_drifts", "python_drifts", "go_drifts",
    "count_drifts", "actions_drifts", "lineending_drifts", "docker_drifts", "docker_multistage_drifts", "docker_bases_drifts",
    "java_drifts", "maven_drifts", "terraform_drifts", "circleci_drifts",
    "gitlab_drifts", "gh_actions_version_drifts", "k8s_drifts", "helm_drifts",
    "dc_drifts", "ci_os_drifts", "dotnet_drifts", "ruby_drifts", "php_drifts",
    "env_drifts",
    "env_example_drifts",
    "compose_override_drifts",
    "helm_values_drifts",
    "external_resource_drifts", "dependabot_drifts",
    "lockfile_drifts", "tool_versions_drifts", "nvmrc_drifts",
    "engines_drifts",
    "swift_drifts", "deno_drifts", "dart_drifts", "makefile_drifts",
    "elixir_drifts", "cmake_drifts", "requirements_drifts", "kotlin_drifts",
    "pipfile_drifts", "conda_drifts", "gradle_catalog_drifts", "jenkins_drifts",
    "ruby_version_drifts", "python_version_drifts", "node_version_drifts",
    "java_version_drifts", "terraform_version_drifts",
    "npmrc_drifts", "yarnrc_drifts", "pnpm_workspace_drifts", "package_manager_drifts",
    "vscode_ext_drifts", "editorconfig_drifts", "git_tag_drifts", "devcontainer_drifts",
    "taskfile_drifts", "mise_drifts",
    "pre_commit_drifts",
    "typosquat_drifts",
    "poetry_drifts",
    "renovate_drifts",
    "bazel_drifts",
    "nix_drifts",
]

# Default configuration
DEFAULT_CONFIG = {
    "exclude_detectors": [],
    "ignore_patterns": [],
    "fail_on_informational": False,
    "doc_paths": None,  # None = auto-detect README.md, CONTRIBUTING.md, docs/README*.md
    "custom_detectors": [],
    "follow_symlinks": True,  # If False, skip symlinks outside repo root during scan
    "max_file_size": 1_000_000,  # 1MB default — files larger than this are skipped (OOM protection)
}


def _parse_toml(text: str) -> dict[str, Any]:
    """Parse TOML config from text using the standard library (tomllib/tomli)."""
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib
    return tomllib.loads(text)


def _coerce_bool(value: Any, default: Any) -> bool:
    """Coerce string/boolean/int to boolean.

    TOML's tomllib strictly types values — a user writing
    ``follow_symlinks = "false"`` (quoted) gets a *string* "false",
    which is truthy in Python. This helper normalizes common
    truthy/falsy strings so config intent is preserved.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in ("false", "no", "0", ""):
            return False
        if value.lower() in ("true", "yes", "1"):
            return True
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def load_config(root: Path = Path(".")) -> dict[str, Any]:
    """Load .driftcheck.toml from repo root, return merged config."""
    cfg = dict(DEFAULT_CONFIG)
    toml_path = root / ".driftcheck.toml"
    if toml_path.exists():
        text = toml_path.read_text(encoding="utf-8")
        raw = _parse_toml(text)
        # Flatten: [driftcheck] section takes top-level precedence
        if "driftcheck" in raw:
            for k, v in raw["driftcheck"].items():
                cfg[k] = v
        for k, v in raw.items():
            if k != "driftcheck" and k not in cfg:
                cfg[k] = v
    # Coerce follow_symlinks so string "false" doesn't become True
    cfg["follow_symlinks"] = _coerce_bool(cfg.get("follow_symlinks"), DEFAULT_CONFIG["follow_symlinks"])
    return cfg


def get_excluded_detectors(config: dict[str, Any]) -> set[str]:
    """Get set of detector keys to exclude based on config."""
    excluded = set()
    for key in config.get("exclude_detectors", []):
        # Support both short names (e.g., "node") and drift keys (e.g., "node_drifts")
        if not key.endswith("_drifts"):
            # Map special short names to actual drift keys
            if key == "rust":
                excluded.add("rust_drifts")
            else:
                excluded.add(f"{key}_drifts")
        else:
            excluded.add(key)
    return excluded


def get_custom_detectors(config: dict[str, Any]) -> list[dict[str, Any]]:
    """Get list of custom detector definitions from config."""
    return config.get("custom_detectors", [])


def get_ignore_patterns(config: dict[str, Any]) -> list[str]:
    """Get list of file glob patterns to ignore during scanning.

    Patterns use fnmatch syntax (e.g., ``*.log``, ``node_modules/*``, ``docs/**/*.md``).
    Files matching any pattern are excluded from walked_files before detectors run.
    """
    return config.get("ignore_patterns", [])


def _matches_ignore_patterns(rel_path: str, patterns: list[str]) -> bool:
    """Check if a relative path matches any ignore pattern (fnmatch syntax)."""
    import fnmatch
    for pattern in patterns:
        if fnmatch.fnmatch(rel_path, pattern):
            return True
        # Also match against basename for simple patterns
        if fnmatch.fnmatch(Path(rel_path).name, pattern):
            return True
    return False

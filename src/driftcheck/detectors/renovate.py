"""Renovate drift detection: renovate.json presence and configuration health.

Detects when a project uses Renovate but has incomplete or problematic configuration.
Returns informational-level drifts for configuration gaps.

Checks:
1. renovate.json exists but has no packageRules (informational)
2. renovate.json has a managerPolicy that blocks all updates (informational)
3. renovate.json has configuration that disables updates globally (informational)
"""

from __future__ import annotations
import json
from pathlib import Path

RENOVATE_FILE = "renovate.json"
RENOVATE_ALT = "renovate.json5"


def find_renovate_drift(root: Path) -> list[dict]:
    """Detect Renovate configuration issues in the repository.

    Returns list of {file, message, drift_key, severity} dicts.
    All findings are informational (non-blocking).
    """
    drifts = []

    for fname in (RENOVATE_FILE, RENOVATE_ALT):
        config_path = root / fname
        if not config_path.is_file():
            continue

        try:
            content = config_path.read_text(encoding="utf-8", errors="replace")
            config = json.loads(content)
        except (json.JSONDecodeError, OSError):
            drifts.append({
                "file": fname,
                "message": f"Could not parse {fname}",
                "drift_key": "renovate_parse_error",
                "severity": "informational",
            })
            continue

        if not isinstance(config, dict):
            drifts.append({
                "file": fname,
                "message": f"{fname} is not a JSON object",
                "drift_key": "renovate_invalid_format",
                "severity": "informational",
            })
            continue

        # Check for packageRules absence (first 8 packageRules are free)
        if "packageRules" not in config:
            drifts.append({
                "file": fname,
                "message": "renovate.json has no packageRules — missing opportunity for custom update policies (first 8 packageRules are free)",
                "drift_key": "renovate_no_package_rules",
                "severity": "informational",
            })

        # Check for overly broad managerPolicy that blocks everything
        manager_policy = config.get("managerPolicy", [])
        if isinstance(manager_policy, list):
            for rule in manager_policy:
                if isinstance(rule, dict):
                    match = rule.get("match", {})
                    if isinstance(match, dict):
                        # Check if this rule blocks all updates
                        if (match.get("updateTypes") == ["none"]
                                or match.get("matchManagers") == ".*"
                                and match.get("enabled") is False):
                            drifts.append({
                                "file": fname,
                                "message": "managerPolicy contains a rule blocking all updates — verify this is intentional",
                                "drift_key": "renovate_blocking_policy",
                                "severity": "informational",
                            })
                            break

        # Check for enabled: false at top level
        if config.get("enabled") is False:
            drifts.append({
                "file": fname,
                "message": "renovate.json has enabled: false at top level — Renovate may not be running for this repo",
                "drift_key": "renovate_disabled",
                "severity": "informational",
            })

    return drifts

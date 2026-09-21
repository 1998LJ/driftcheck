"""package.json vs package-lock.json integrity drift detection."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

_ALT_NODE_LOCKFILES = ("yarn.lock", "pnpm-lock.yaml", "bun.lock", "bun.lockb")
_VERSION_RE = re.compile(
    r"^[v=]?(?P<major>\d+)(?:\.(?P<minor>\d+|x|X|\*))?(?:\.(?P<patch>\d+|x|X|\*))?"
)


def _parse_version(value: str) -> tuple[int, int, int] | None:
    """Parse the numeric core of a semver string."""
    match = _VERSION_RE.match(value.strip())
    if not match:
        return None
    parts = []
    for name in ("major", "minor", "patch"):
        raw = match.group(name)
        if raw is None or raw.lower() == "x" or raw == "*":
            parts.append(0)
        else:
            parts.append(int(raw))
    return tuple(parts)


def _partial_parts(value: str) -> tuple[list[int], int] | None:
    """Return parsed numeric parts and count of explicitly specified parts."""
    raw = value.strip().lstrip("v=")
    core = re.split(r"[-+]", raw, maxsplit=1)[0]
    tokens = core.split(".")
    values: list[int] = []
    specified = 0
    for token in tokens[:3]:
        if token.lower() == "x" or token == "*":
            break
        if not token.isdigit():
            return None
        values.append(int(token))
        specified += 1
    while len(values) < 3:
        values.append(0)
    return values, specified


def _compare(version: tuple[int, int, int], operator: str, bound: tuple[int, int, int]) -> bool:
    if operator in ("", "="):
        return version == bound
    if operator == ">=":
        return version >= bound
    if operator == ">":
        return version > bound
    if operator == "<=":
        return version <= bound
    if operator == "<":
        return version < bound
    raise ValueError(f"unsupported comparator: {operator}")


def _satisfies_atom(version: tuple[int, int, int], atom: str) -> bool | None:
    atom = atom.strip()
    if not atom or atom in {"*", "x", "X"}:
        return True

    if atom.startswith("^"):
        parsed = _partial_parts(atom[1:])
        if parsed is None:
            return None
        values, _ = parsed
        lower = tuple(values)
        major, minor, patch = lower
        if major > 0:
            upper = (major + 1, 0, 0)
        elif minor > 0:
            upper = (0, minor + 1, 0)
        else:
            upper = (0, 0, patch + 1)
        return lower <= version < upper

    if atom.startswith("~"):
        parsed = _partial_parts(atom[1:])
        if parsed is None:
            return None
        values, specified = parsed
        lower = tuple(values)
        if specified <= 1:
            upper = (values[0] + 1, 0, 0)
        else:
            upper = (values[0], values[1] + 1, 0)
        return lower <= version < upper

    comparator = re.match(r"^(>=|<=|>|<|=)?\s*(.+)$", atom)
    if comparator is None:
        return None
    operator = comparator.group(1) or ""
    raw_version = comparator.group(2).strip()

    parsed = _partial_parts(raw_version)
    if parsed is None:
        return None
    values, specified = parsed
    bound = tuple(values)

    # Bare partial versions and wildcard versions are npm-style prefix ranges.
    wildcard = any(part in raw_version.lower() for part in ("x", "*"))
    if operator == "" and (wildcard or specified < 3):
        if specified == 1:
            return version[0] == values[0]
        if specified == 2:
            return version[:2] == tuple(values[:2])
        return True

    return _compare(version, operator, bound)


def satisfies_npm_range(version: str, spec: str) -> bool | None:
    """Return whether *version* satisfies a common npm semver range.

    Unsupported non-semver sources (git URLs, file paths, npm aliases, tags)
    return None so callers can skip them rather than report false positives.
    """
    parsed_version = _parse_version(version)
    if parsed_version is None:
        return None

    spec = spec.strip()
    if not spec or spec in {"*", "latest"}:
        return True
    if spec.startswith(("file:", "git", "http:", "https:", "workspace:", "npm:")):
        return None

    branches = [branch.strip() for branch in spec.split("||")]
    branch_results: list[bool | None] = []
    for branch in branches:
        hyphen = re.fullmatch(r"\s*(\S+)\s+-\s+(\S+)\s*", branch)
        if hyphen:
            low = _parse_version(hyphen.group(1))
            high = _parse_version(hyphen.group(2))
            branch_results.append(
                None if low is None or high is None else low <= parsed_version <= high
            )
            continue

        atoms = [part for part in branch.replace(",", " ").split() if part]
        if not atoms:
            branch_results.append(True)
            continue
        results = [_satisfies_atom(parsed_version, atom) for atom in atoms]
        if any(result is False for result in results):
            branch_results.append(False)
        elif all(result is True for result in results):
            branch_results.append(True)
        else:
            branch_results.append(None)

    if any(result is True for result in branch_results):
        return True
    if branch_results and all(result is False for result in branch_results):
        return False
    return None


def _declared_dependencies(package_data: dict) -> dict[str, str]:
    declared: dict[str, str] = {}
    for field in ("dependencies", "devDependencies", "optionalDependencies"):
        values = package_data.get(field, {})
        if isinstance(values, dict):
            for name, spec in values.items():
                if isinstance(name, str) and isinstance(spec, str):
                    declared[name] = spec
    return declared


def _resolved_dependencies(lock_data: dict) -> dict[str, str]:
    resolved: dict[str, str] = {}
    lockfile_version = lock_data.get("lockfileVersion", 1)

    if isinstance(lockfile_version, int) and lockfile_version >= 2:
        packages = lock_data.get("packages", {})
        if isinstance(packages, dict):
            for path, metadata in packages.items():
                if not isinstance(path, str) or not path.startswith("node_modules/"):
                    continue
                if not isinstance(metadata, dict):
                    continue
                version = metadata.get("version")
                if not isinstance(version, str):
                    continue
                name = path[len("node_modules/") :]
                # Only use direct/root node_modules entries. Nested entries contain
                # another "/node_modules/" segment and are transitive resolutions.
                if "/node_modules/" not in name:
                    resolved[name] = version

    dependencies = lock_data.get("dependencies", {})
    if isinstance(dependencies, dict):
        for name, metadata in dependencies.items():
            if not isinstance(name, str) or not isinstance(metadata, dict):
                continue
            version = metadata.get("version")
            if isinstance(version, str):
                resolved.setdefault(name, version)
    return resolved


def find_package_lock_drift(root: Path) -> list[dict]:
    """Detect package.json/package-lock.json lifecycle and range-integrity drift."""
    package_path = root / "package.json"
    lock_path = root / "package-lock.json"

    if not package_path.exists():
        if lock_path.exists():
            return [{
                "file": "package-lock.json",
                "kind": "lockfile_orphaned",
                "detail": "orphaned package-lock.json — no package.json found",
                "pos": 0,
            }]
        return []

    try:
        package_data = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if not lock_path.exists():
        # Do not require an npm lockfile for projects that clearly use another
        # Node package manager.
        if any((root / name).exists() for name in _ALT_NODE_LOCKFILES):
            return []
        return [{
            "file": "package-lock.json",
            "kind": "lockfile_missing",
            "detail": "missing package-lock.json — package.json exists but no Node lockfile found",
            "pos": 0,
        }]

    drifts: list[dict] = []
    try:
        if os.path.getmtime(lock_path) < os.path.getmtime(package_path):
            drifts.append({
                "file": "package-lock.json",
                "kind": "lockfile_stale",
                "detail": "stale package-lock.json — older than package.json (run npm install to regenerate)",
                "pos": 0,
            })
    except OSError:
        pass

    try:
        lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        drifts.append({
            "file": "package-lock.json",
            "kind": "lockfile_invalid",
            "detail": "package-lock.json is not valid JSON",
            "pos": 0,
        })
        return drifts

    declared = _declared_dependencies(package_data)
    resolved = _resolved_dependencies(lock_data)

    for name, spec in sorted(declared.items()):
        if spec.strip().startswith(("file:", "git", "http:", "https:", "workspace:", "npm:")):
            continue

        resolved_version = resolved.get(name)
        if resolved_version is None:
            drifts.append({
                "file": "package-lock.json",
                "kind": "lockfile_dependency_missing",
                "dependency": name,
                "declared": spec,
                "detail": f"{name} is declared in package.json but missing from package-lock.json",
                "pos": 0,
            })
            continue

        satisfies = satisfies_npm_range(resolved_version, spec)
        if satisfies is False:
            drifts.append({
                "file": "package-lock.json",
                "kind": "lockfile_range_violation",
                "dependency": name,
                "declared": spec,
                "resolved": resolved_version,
                "detail": f"{name}@{resolved_version} does not satisfy package.json range {spec}",
                "pos": 0,
            })

    return drifts

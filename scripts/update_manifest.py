"""Update MANIFEST.md counts automatically by scanning the codebase.

Usage:
    python scripts/update_manifest.py

Counts:
1. Detector module files in src/driftcheck/detectors/ (excluding __init__.py)
2. DRIFT_KEYS entries in src/driftcheck/config.py
3. find_* names imported in src/driftcheck/__init__.py (the public API surface)
4. Test functions (def test_*) in tests/

Updates MANIFEST.md in place. Safe to run as a pre-commit hook or CI check.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path


def count_detector_files(src_dir: Path) -> int:
    """Count .py files in detectors/ excluding __init__.py."""
    detectors_dir = src_dir / "driftcheck" / "detectors"
    if not detectors_dir.exists():
        return 0
    return len([f for f in detectors_dir.glob("*.py") if f.name != "__init__.py" and f.name != "__pycache__"])


def count_drift_keys(src_dir: Path) -> int:
    """Count entries in DRIFT_KEYS from config.py (parsed via AST)."""
    config_file = src_dir / "driftcheck" / "config.py"
    if not config_file.exists():
        return 0
    tree = ast.parse(config_file.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "DRIFT_KEYS":
                    if isinstance(node.value, ast.List):
                        return len(node.value.elts)
    return 0


def count_exported_find(src_dir: Path) -> int:
    """Count find_* names imported in __init__.py (the public API surface)."""
    init_file = src_dir / "driftcheck" / "__init__.py"
    if not init_file.exists():
        return 0
    tree = ast.parse(init_file.read_text())
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                if alias.name.startswith("find_"):
                    count += 1
        elif isinstance(node, ast.FunctionDef) and node.name.startswith("find_"):
            count += 1
    return count


def count_tests(tests_dir: Path) -> int:
    """Count def test_* functions across all test files."""
    if not tests_dir.exists():
        return 0
    total = 0
    for f in tests_dir.rglob("test_*.py"):
        text = f.read_text()
        total += len(re.findall(r'def test_', text))
    return total


def update_manifest(manifest_path: Path, drift: int, keys: int, funcs: int, tests: int) -> None:
    """Update counts in MANIFEST.md."""
    text = manifest_path.read_text()

    text = re.sub(r'\*\*\d+ detector modules\*\*', f'**{drift} detector modules**', text)
    text = re.sub(r'\*\*\d+ registered detectors\*\*', f'**{keys} registered detectors**', text)
    text = re.sub(r'\*\*\d+ find_\* functions\*\*', f'**{funcs} find_* functions**', text)
    text = re.sub(r'\*\*\d+ tests\*\*', f'**{tests} tests**', text)
    text = re.sub(r'\*\*\d+ detector module files\*\*', f'**{drift} detector module files**', text)
    text = re.sub(r'All \d+ detector modules', f'All {drift} detector modules', text)

    manifest_path.write_text(text)
    print(f"Updated {manifest_path}: {drift} modules, {keys} keys, {funcs} funcs, {tests} tests")


def main() -> None:
    root = Path(__file__).parent.parent
    src_dir = root / "src"
    tests_dir = root / "tests"
    manifest_path = root / "MANIFEST.md"

    drift = count_detector_files(src_dir)
    keys = count_drift_keys(src_dir)
    funcs = count_exported_find(src_dir)
    tests = count_tests(tests_dir)

    print(f"Detected: {drift} detector files, {keys} DRIFT_KEYS, {funcs} find_* exports, {tests} tests")
    update_manifest(manifest_path, drift, keys, funcs, tests)


if __name__ == "__main__":
    main()

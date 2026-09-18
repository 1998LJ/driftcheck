# API Reference

driftcheck exposes a Python API for embedding drift detection in scripts, CI pipelines, and custom tools.

## Package

```python
import driftcheck

print(driftcheck.__version__)  # e.g. "0.1.45"
```

All public detector functions are importable from the top level.

---

## Types

### `Drift`

A single detected drift.

```python
@dataclass
class Drift:
    file: str          # file where drift was found
    line: int          # line number (1-indexed)
    detector: str      # detector key (e.g. "rust_drifts")
    message: str       # human-readable description
    severity: str      # "info", "warning", "error"
    expected: str      # value from toolchain
    actual: str        # value found in docs
    fix: str | None    # suggested fix text
```

### `DriftcheckResult`

Container for a full scan result.

```python
@dataclass
class DriftcheckResult:
    repo_path: str
    drifts: list[Drift]
    detectors_run: int
    duration_seconds: float

    @property
    def has_drift(self) -> bool: ...
    def to_json(self) -> str: ...
    def to_csv(self) -> str: ...
    def to_sarif(self) -> dict: ...
    def to_markdown(self) -> str: ...
```

---

## Core Functions

### `scan_repository(repo_path: str, ...) -> DriftcheckResult`

Run all detectors against a repository.

```python
from driftcheck import scan_repository

result = scan_repository("/path/to/repo")
print(f"Found {len(result.drifts)} drifts")
for drift in result.drifts:
    print(f"  {drift.file}:{drift.line}  {drift.message}")
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `repo_path` | `str` | required | Path to the repository root |
| `only` | `list[str] \| None` | `None` | Run only these detectors |
| `exclude` | `list[str] \| None` | `None` | Skip these detectors |
| `fail_on_informational` | `bool` | `False` | Treat info drifts as blocking |
| `config_path` | `str \| None` | `None` | Path to `.driftcheck.toml` |

**Returns:** `DriftcheckResult`

---

### `scan_file(file_path: str, source: str, detectors: list[str] | None = None) -> list[Drift]`

Scan a single file for drift.

```python
from driftcheck import scan_file

drifts = scan_file("README.md", open("README.md").read(), detectors=["rust_drifts"])
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `file_path` | `str` | required | Path to the file (for reporting) |
| `source` | `str` | required | File contents |
| `detectors` | `list[str] \| None` | `None` | Which detectors to run |

**Returns:** `list[Drift]`

---

## Output Functions

### `to_sarif(drifts: list[Drift], repo_path: str) -> dict`

Convert drifts to SARIF 2.1.0 format for GitHub Code Scanning.

```python
from driftcheck import to_sarif

sarif = to_sarif(drifts, repo_path="/path/to/repo")
import json
with open("driftcheck.sarif", "w") as f:
    json.dump(sarif, f, indent=2)
```

---

### `to_csv(drifts: list[Drift]) -> str`

Convert drifts to CSV.

```python
from driftcheck import to_csv

csv_output = to_csv(drifts)
with open("drifts.csv", "w") as f:
    f.write(csv_output)
```

**Columns:** `file`, `line`, `detector`, `severity`, `expected`, `actual`, `message`

---

### `to_markdown(drifts: list[Drift]) -> str`

Generate a markdown summary for CI job summaries or PR comments.

```python
from driftcheck import to_markdown

summary = to_markdown(drifts)
print(summary)
```

---

## Configuration

### `load_config(repo_path: str) -> dict`

Load `.driftcheck.toml` configuration.

```python
from driftcheck import load_config

config = load_config("/path/to/repo")
print(config["driftcheck"]["exclude_detectors"])
```

**Returns:** Nested dict matching the TOML structure.

---

### `Config`

Configuration dataclass.

```python
@dataclass
class Config:
    exclude_detectors: list[str]
    fail_on_informational: bool
    doc_paths: list[str]
```

---

## Detector Registry

### `list_detectors() -> list[str]`

List all registered detector keys.

```python
from driftcheck import list_detectors

for detector in list_detectors():
    print(detector)
```

**Returns:** Sorted list of detector keys (e.g. `["rust_drifts", "node_drifts", ...]`)

---

### `get_detector(key: str) -> Detector`

Get a detector by key.

```python
from driftcheck import get_detector

detector = get_detector("rust_drifts")
print(detector.description)
print(detector.severity)
```

---

## Individual Detectors

Each detector is a standalone function that takes `(source: str, docs: dict[str, str])` and returns `list[Drift]`.

### `find_rust_drift(source: dict[str, str], docs: dict[str, str]) -> list[Drift]`

```python
from driftcheck import find_rust_drift

source = {"rust-toolchain.toml": "channel = \"1.96.1\""}
docs = {"README.md": "Rust 1.93.0"}
drifts = find_rust_drift(source, docs)
```

### `find_node_drift(source: dict[str, str], docs: dict[str, str]) -> list[Drift]`

```python
from driftcheck import find_node_drift

source = {"package.json": '{"engines": {"node": ">=24"}}'}
docs = {"README.md": "Node.js 18"}
drifts = find_node_drift(source, docs)
```

> See `driftcheck --list-detectors` for all 68 registered detectors.

---

## Plugins

### `register_detector(key: str, func: Callable, description: str = "", severity: str = "warning") -> None`

Register a custom detector at runtime.

```python
from driftcheck import register_detector, scan_repository

def my_detector(source, docs):
    # return list[Drift]
    ...

register_detector("my_detector", my_detector, "My custom drift check")

result = scan_repository(".")  # includes my_detector
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | No drift |
| 1 | Drift detected |
| 2 | Error (invalid args, missing repo) |

```python
import sys
from driftcheck import scan_repository

result = scan_repository(".")
if result.has_drift:
    print("Drift detected!")
    for d in result.drifts:
        print(f"  {d.file}:{d.line}: {d.message}")
    sys.exit(1)
```

---

## Full Example

```python
#!/usr/bin/env python3
"""Embed driftcheck in a CI pipeline."""

import json
import sys

from driftcheck import scan_repository, to_sarif, to_csv

def main():
    result = scan_repository(
        ".",
        exclude=["ci_os_drifts", "nvmrc_drifts"],
        fail_on_informational=False,
    )

    # Markdown summary
    print(result.to_markdown())

    # SARIF for GitHub Code Scanning
    with open("driftcheck.sarif", "w") as f:
        json.dump(result.to_sarif(), f, indent=2)

    # CSV for spreadsheets
    with open("drifts.csv", "w") as f:
        f.write(result.to_csv())

    if result.has_drift:
        sys.exit(1)

if __name__ == "__main__":
    main()
```

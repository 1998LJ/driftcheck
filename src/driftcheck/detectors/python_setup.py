"""Legacy Python packaging drift detection for setup.py and setup.cfg."""
from __future__ import annotations

import ast
import configparser
import re

from .python import PY_RE

_VERSION_RE = re.compile(r"(?P<ver>\d+\.\d+(?:\.\d+)?)")
_REQ_RE = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9_.-]+)\s*(?P<op>==|>=|~=)\s*(?P<ver>\d+(?:\.\d+){1,2})"
)


def _version_tuple(version: str) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError:
        return (0,)


def _floor_from_spec(spec: str | None) -> str | None:
    if not spec:
        return None
    match = _VERSION_RE.search(spec)
    return match.group("ver") if match else None


def _requirement_pins(values: list[str]) -> dict[str, tuple[str, str]]:
    pins: dict[str, tuple[str, str]] = {}
    for value in values:
        match = _REQ_RE.match(value)
        if match:
            name = match.group("name").lower().replace("_", "-")
            pins[name] = (match.group("op"), match.group("ver"))
    return pins


def parse_setup_py(text: str) -> tuple[str | None, dict[str, tuple[str, str]]]:
    """Safely extract python_requires and literal install_requires from setup.py."""
    if not text.strip():
        return None, {}
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None, {}

    python_requires: str | None = None
    requirements: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func_name = (
            node.func.id
            if isinstance(node.func, ast.Name)
            else node.func.attr
            if isinstance(node.func, ast.Attribute)
            else ""
        )
        if func_name != "setup":
            continue
        for keyword in node.keywords:
            if keyword.arg == "python_requires" and isinstance(keyword.value, ast.Constant):
                if isinstance(keyword.value.value, str):
                    python_requires = keyword.value.value
            elif keyword.arg == "install_requires" and isinstance(
                keyword.value, (ast.List, ast.Tuple)
            ):
                for item in keyword.value.elts:
                    if isinstance(item, ast.Constant) and isinstance(item.value, str):
                        requirements.append(item.value)

    return _floor_from_spec(python_requires), _requirement_pins(requirements)


def parse_setup_cfg(text: str) -> tuple[str | None, dict[str, tuple[str, str]]]:
    """Extract python_requires and install_requires from setup.cfg."""
    if not text.strip():
        return None, {}
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read_string(text)
    except configparser.Error:
        return None, {}
    if not parser.has_section("options"):
        return None, {}

    python_requires = _floor_from_spec(parser.get("options", "python_requires", fallback=None))
    raw_requirements = parser.get("options", "install_requires", fallback="")
    requirements = [
        line.strip()
        for line in raw_requirements.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    return python_requires, _requirement_pins(requirements)


def _dependency_doc_pattern(package: str) -> re.Pattern[str]:
    package_pattern = re.escape(package).replace(r"\-", "[-_.]")
    return re.compile(
        rf"(?i)\b{package_pattern}\s*(?P<op>==|>=|~=)\s*(?P<ver>\d+(?:\.\d+){{1,2}})"
    )


def find_python_setup_drift(
    setup_py_text: str | None,
    setup_cfg_text: str | None,
    docs: dict[str, str],
) -> list[dict]:
    """Detect setup.py/setup.cfg Python and dependency version drift in docs."""
    py_floor, py_requirements = parse_setup_py(setup_py_text or "")
    cfg_floor, cfg_requirements = parse_setup_cfg(setup_cfg_text or "")

    # setup.py is the requested source of truth when it declares a value;
    # setup.cfg fills gaps for declarative/legacy projects.
    floor = py_floor or cfg_floor
    floor_source = "setup.py" if py_floor else "setup.cfg" if cfg_floor else None
    requirements = dict(cfg_requirements)
    requirements.update(py_requirements)
    requirement_sources = {
        name: ("setup.py" if name in py_requirements else "setup.cfg")
        for name in requirements
    }

    drifts: list[dict] = []
    for filename, content in docs.items():
        if floor is not None and floor_source is not None:
            for match in PY_RE.finditer(content):
                doc_version = match.group("ver")
                if _version_tuple(doc_version) < _version_tuple(floor):
                    drifts.append(
                        {
                            "file": filename,
                            "type": "python_requires",
                            "doc_version": doc_version,
                            "setup_version": floor,
                            "source": floor_source,
                            "pos": match.start(),
                        }
                    )
                    break

        for package, (setup_op, setup_version) in requirements.items():
            pattern = _dependency_doc_pattern(package)
            for match in pattern.finditer(content):
                doc_version = match.group("ver")
                doc_op = match.group("op")
                mismatch = (
                    doc_version != setup_version
                    if setup_op == "=="
                    else _version_tuple(doc_version) < _version_tuple(setup_version)
                )
                if mismatch:
                    drifts.append(
                        {
                            "file": filename,
                            "type": "install_requires",
                            "package": package,
                            "doc_version": doc_version,
                            "doc_operator": doc_op,
                            "setup_version": setup_version,
                            "setup_operator": setup_op,
                            "source": requirement_sources[package],
                            "pos": match.start(),
                        }
                    )
                    break

    return drifts

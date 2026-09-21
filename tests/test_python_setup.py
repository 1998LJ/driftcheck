"""Tests for legacy Python setup.py/setup.cfg drift detection."""
from driftcheck.detector import scan_repo
from driftcheck.detectors.fix import apply_fixes
from driftcheck.detectors.python_setup import (
    find_python_setup_drift,
    parse_setup_cfg,
    parse_setup_py,
)


def test_parse_setup_py_python_requires():
    floor, requirements = parse_setup_py(
        'from setuptools import setup\n'
        'setup(python_requires=">=3.10", install_requires=["requests>=2.31"])\n'
    )
    assert floor == "3.10"
    assert requirements == {"requests": (">=", "2.31")}


def test_parse_setup_cfg_options():
    floor, requirements = parse_setup_cfg(
        "[options]\n"
        "python_requires = >=3.9\n"
        "install_requires =\n"
        "    requests>=2.30\n"
        "    click==8.1\n"
    )
    assert floor == "3.9"
    assert requirements["requests"] == (">=", "2.30")
    assert requirements["click"] == ("==", "8.1")


def test_setup_py_python_floor_drift():
    docs = {"README.md": "Requires Python 3.9 or newer."}
    drifts = find_python_setup_drift(
        'from setuptools import setup\nsetup(python_requires=">=3.10")',
        None,
        docs,
    )
    assert drifts == [
        {
            "file": "README.md",
            "type": "python_requires",
            "doc_version": "3.9",
            "setup_version": "3.10",
            "source": "setup.py",
            "pos": docs["README.md"].index("Python"),
        }
    ]


def test_setup_cfg_python_floor_drift():
    drifts = find_python_setup_drift(
        None,
        "[options]\npython_requires = >=3.11\n",
        {"CONTRIBUTING.md": "Development requires Python 3.10."},
    )
    assert len(drifts) == 1
    assert drifts[0]["source"] == "setup.cfg"
    assert drifts[0]["setup_version"] == "3.11"


def test_newer_documented_python_version_is_not_drift():
    drifts = find_python_setup_drift(
        'from setuptools import setup\nsetup(python_requires=">=3.10")',
        None,
        {"README.md": "Tested with Python 3.12."},
    )
    assert drifts == []


def test_install_requires_pin_drift():
    drifts = find_python_setup_drift(
        'from setuptools import setup\n'
        'setup(install_requires=["requests>=2.31", "click==8.1"])',
        None,
        {"README.md": "Install with pip install requests>=2.28 click==8.0."},
    )
    assert {(d["package"], d["setup_version"]) for d in drifts} == {
        ("requests", "2.31"),
        ("click", "8.1"),
    }


def test_setup_py_takes_precedence_over_setup_cfg():
    drifts = find_python_setup_drift(
        'from setuptools import setup\nsetup(python_requires=">=3.11")',
        "[options]\npython_requires = >=3.9\n",
        {"README.md": "Requires Python 3.10."},
    )
    assert len(drifts) == 1
    assert drifts[0]["source"] == "setup.py"
    assert drifts[0]["setup_version"] == "3.11"


def test_dynamic_setup_py_is_ignored_safely():
    floor, requirements = parse_setup_py(
        'from setuptools import setup\n'
        'minimum = ">=3.10"\n'
        'setup(python_requires=minimum, install_requires=get_requirements())\n'
    )
    assert floor is None
    assert requirements == {}


def test_scan_repo_registers_python_setup_drift(tmp_path):
    (tmp_path / "setup.py").write_text(
        'from setuptools import setup\nsetup(python_requires=">=3.11")\n'
    )
    (tmp_path / "README.md").write_text("Requires Python 3.10.\n")

    result = scan_repo(tmp_path)
    assert result["python_setup_drifts"]
    assert result["python_setup_drifts"][0]["setup_version"] == "3.11"


def test_apply_fixes_updates_python_setup_version(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("Requires Python 3.9 or newer.\n")
    result = {
        "python_setup_drifts": [
            {
                "file": "README.md",
                "type": "python_requires",
                "doc_version": "3.9",
                "setup_version": "3.11",
                "source": "setup.py",
            }
        ]
    }

    assert apply_fixes(tmp_path, result) == ["README.md"]
    assert "Python 3.11" in readme.read_text()

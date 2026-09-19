"""Tests for .driftcheck.toml configuration loading."""
from __future__ import annotations
import tempfile
from pathlib import Path

from driftcheck.config import load_config, get_excluded_detectors, _parse_toml, _coerce_bool


class TestCoerceBool:
    def test_bool_false(self):
        assert _coerce_bool(False, True) is False

    def test_bool_true(self):
        assert _coerce_bool(True, False) is True

    def test_string_false_lowercase(self):
        assert _coerce_bool("false", True) is False

    def test_string_False_mixed_case(self):
        assert _coerce_bool("False", True) is False

    def test_string_no(self):
        assert _coerce_bool("no", True) is False

    def test_string_zero(self):
        assert _coerce_bool("0", True) is False

    def test_string_empty(self):
        assert _coerce_bool("", True) is False

    def test_string_true_lowercase(self):
        assert _coerce_bool("true", False) is True

    def test_string_True_mixed_case(self):
        assert _coerce_bool("True", False) is True

    def test_string_yes(self):
        assert _coerce_bool("yes", False) is True

    def test_string_one(self):
        assert _coerce_bool("1", False) is True

    def test_int_0(self):
        assert _coerce_bool(0, True) is False

    def test_int_1(self):
        assert _coerce_bool(1, False) is True

    def test_float_zero(self):
        assert _coerce_bool(0.0, True) is False

    def test_none_uses_default(self):
        assert _coerce_bool(None, True) is True
        assert _coerce_bool(None, False) is False

    def test_garbage_string_uses_default(self):
        assert _coerce_bool("garbage", True) is True
        assert _coerce_bool("garbage", False) is False


class TestParseToml:
    def test_empty(self):
        assert _parse_toml("") == {}

    def test_comments_only(self):
        assert _parse_toml("# comment\n") == {}

    def test_simple_key_value(self):
        result = _parse_toml('name = "test"')
        assert result == {"name": "test"}

    def test_boolean(self):
        result = _parse_toml("verbose = true\ndebug = false")
        assert result == {"verbose": True, "debug": False}

    def test_list(self):
        result = _parse_toml('exclude = ["node", "python"]')
        assert result == {"exclude": ["node", "python"]}

    def test_section(self):
        text = '[driftcheck]\nexclude = ["node"]\nverbose = true'
        result = _parse_toml(text)
        assert result == {"driftcheck": {"exclude": ["node"], "verbose": True}}

    def test_multiline_array(self):
        """Multi-line arrays are supported by tomllib (issue #151)."""
        text = 'exclude = [\n    "node",\n    "python",\n]'
        result = _parse_toml(text)
        assert result == {"exclude": ["node", "python"]}

    def test_nested_section(self):
        """Nested TOML sections work with tomllib (issue #151)."""
        text = '[driftcheck]\nverbose = true\n\n[driftcheck.custom]\nkey = "value"'
        result = _parse_toml(text)
        assert result == {"driftcheck": {"verbose": True, "custom": {"key": "value"}}}


class TestLoadConfig:
    def test_no_config_file(self):
        with tempfile.TemporaryDirectory() as td:
            config = load_config(Path(td))
            assert config["exclude_detectors"] == []

    def test_exclude_rust_detector(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".driftcheck.toml").write_text(
                '[driftcheck]\nexclude_detectors = ["rust"]\n'
            )
            config = load_config(root)
            excluded = get_excluded_detectors(config)
            # "rust" maps to "rust_drifts"
            assert excluded == {"rust_drifts"}

    def test_fail_on_informational(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".driftcheck.toml").write_text(
                '[driftcheck]\nfail_on_informational = true\n'
            )
            config = load_config(root)
            assert config["fail_on_informational"] is True

    def test_with_scan_repo(self):
        """Test that scan_repo reads and applies .driftcheck.toml config."""
        from driftcheck.detector import scan_repo
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # Set up a repo with both rust and node
            (root / "rust-toolchain.toml").write_text('channel = "1.96.1"')
            (root / "package.json").write_text('{"engines": {"node": "24.x"}}')
            (root / "README.md").write_text("Rust 1.96.1 and Node 24")
            # Exclude rust detector
            (root / ".driftcheck.toml").write_text(
                '[driftcheck]\nexclude_detectors = ["rust"]\n'
            )
            result = scan_repo(root)
            # rust_drifts should be excluded (not in result)
            assert "rust_drifts" not in result
            # node drifts should still be present
            assert "node_drifts" in result


    def test_follow_symlinks_string_false_coerced(self):
        """Issue #187: string 'false' must be coerced to bool False."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".driftcheck.toml").write_text(
                '[driftcheck]\nfollow_symlinks = "false"\n'
            )
            config = load_config(root)
            assert config["follow_symlinks"] is False

    def test_follow_symlinks_bool_false_untouched(self):
        """Bool false stays False (no coercion needed)."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".driftcheck.toml").write_text(
                '[driftcheck]\nfollow_symlinks = false\n'
            )
            config = load_config(root)
            assert config["follow_symlinks"] is False

    def test_follow_symlinks_bool_true_untouched(self):
        """Bool true stays True."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".driftcheck.toml").write_text(
                '[driftcheck]\nfollow_symlinks = true\n'
            )
            config = load_config(root)
            assert config["follow_symlinks"] is True


class TestIgnorePatterns:
    """Issue #144: ignore_patterns config option is parsed but never applied."""

    def test_ignore_patterns_default_empty(self):
        """Default config has no ignore patterns."""
        with tempfile.TemporaryDirectory() as td:
            config = load_config(Path(td))
            assert config["ignore_patterns"] == []

    def test_ignore_patterns_parsed_from_toml(self):
        """ignore_patterns is loaded from .driftcheck.toml."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".driftcheck.toml").write_text(
                '[driftcheck]\nignore_patterns = ["*.log", "node_modules/*"]\n'
            )
            config = load_config(root)
            assert config["ignore_patterns"] == ["*.log", "node_modules/*"]

    def test_ignore_patterns_filters_walked_files(self):
        """Files matching ignore_patterns are excluded from scan."""
        from driftcheck.detector import scan_repo
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            # Create a README with drift (pyproject 3.12 vs README 3.11)
            readme = root / "README.md"
            readme.write_text("# Test\nPython 3.11\n")
            pyproject = root / "pyproject.toml"
            pyproject.write_text('[project]\nrequires-python = ">=3.12"\n')
            # Create a file that would be picked up by custom doc_paths
            old_doc = root / "old-docs.md"
            old_doc.write_text("Python 3.8\n")
            # Configure ignore_patterns + custom doc_paths that would pick it up
            (root / ".driftcheck.toml").write_text(
                '[driftcheck]\n'
                'ignore_patterns = ["old-docs.md"]\n'
                'doc_paths = ["old-docs.md"]\n'
            )
            result = scan_repo(root)
            # The python drift should still be detected (pyproject 3.12 vs README 3.11)
            assert result.get("python_drifts", []) != []
            # Check that the ignored file content isn't in docs
            for doc_content in result.get("docs", {}).values():
                assert "Python 3.8" not in doc_content

    def test_matches_ignore_patterns(self):
        """Unit test the _matches_ignore_patterns helper."""
        from driftcheck.config import _matches_ignore_patterns
        assert _matches_ignore_patterns("foo.log", ["*.log"]) is True
        assert _matches_ignore_patterns("foo.txt", ["*.log"]) is False
        assert _matches_ignore_patterns("node_modules/foo", ["node_modules/*"]) is True
        assert _matches_ignore_patterns("docs/CHANGELOG.md", ["*.md"]) is True  # basename match
        assert _matches_ignore_patterns("src/main.py", ["CHANGELOG.md"]) is False

    def test_ignore_patterns_does_not_block_matching(self):
        """Files NOT matching ignore_patterns are still scanned."""
        from driftcheck.detector import scan_repo
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            readme = root / "README.md"
            readme.write_text("# Test\nPython 3.12\n")
            pyproject = root / "pyproject.toml"
            pyproject.write_text('[project]\nrequires-python = ">=3.12"\n')
            # No Python drift expected (README matches pyproject floor)
            (root / ".driftcheck.toml").write_text(
                '[driftcheck]\nignore_patterns = ["CHANGELOG.md"]\n'
            )
            result = scan_repo(root)
            # With matching versions, python_drifts should be empty
            assert result.get("python_drifts", []) == []

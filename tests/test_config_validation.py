"""Tests for config validation."""
import pytest
from pathlib import Path
from driftcheck.config import (
    load_config,
    validate_config,
    ConfigValidationError,
    DEFAULT_CONFIG,
)


class TestValidateConfig:
    """Tests for validate_config() function."""

    def test_empty_config_is_valid(self):
        """Empty config should produce no warnings."""
        warnings = validate_config({})
        assert warnings == []

    def test_valid_known_keys(self):
        """All known config keys should be accepted."""
        raw = {
            "exclude_detectors": ["node_drifts"],
            "ignore_patterns": ["*.log"],
            "fail_on_informational": True,
            "follow_symlinks": False,
            "max_file_size": 2000000,
            "custom_detectors": [],
        }
        warnings = validate_config(raw)
        assert warnings == []

    def test_unknown_key_warns_in_non_strict_mode(self):
        """Unknown keys should produce warnings in non-strict mode."""
        raw = {"ignore_paterns": ["*.log"]}  # Typo: should be ignore_patterns
        warnings = validate_config(raw, strict=False)
        assert len(warnings) == 1
        assert "ignore_paterns" in warnings[0]
        assert "Unknown config key" in warnings[0]

    def test_unknown_key_raises_in_strict_mode(self):
        """Unknown keys should raise ConfigValidationError in strict mode."""
        raw = {"ignore_paterns": ["*.log"]}
        with pytest.raises(ConfigValidationError, match="ignore_paterns"):
            validate_config(raw, strict=True)

    def test_multiple_unknown_keys(self):
        """Multiple unknown keys should all be reported."""
        raw = {
            "ignore_paterns": [],
            "fail_on_infomational": True,  # Typo
        }
        warnings = validate_config(raw, strict=False)
        assert len(warnings) == 2

    def test_invalid_bool_type(self):
        """Non-bool/int/str values for bool keys should warn."""
        raw = {"fail_on_informational": [1, 2, 3]}  # List is invalid
        warnings = validate_config(raw, strict=False)
        assert any("fail_on_informational" in w for w in warnings)

    def test_invalid_int_type(self):
        """Non-int values for int keys should warn."""
        raw = {"max_file_size": "1000000"}  # String instead of int
        warnings = validate_config(raw, strict=False)
        assert any("max_file_size" in w for w in warnings)

    def test_invalid_list_type(self):
        """Non-list values for list keys should warn."""
        raw = {"ignore_patterns": "*.log"}  # String instead of list
        warnings = validate_config(raw, strict=False)
        assert any("ignore_patterns" in w for w in warnings)

    def test_valid_types_no_warnings(self):
        """Valid types should produce no warnings."""
        raw = {
            "fail_on_informational": True,
            "follow_symlinks": "false",  # String coerced to bool
            "max_file_size": 500000,
            "ignore_patterns": ["*.log", "node_modules/*"],
            "exclude_detectors": ["node_drifts"],
            "doc_paths": None,
        }
        warnings = validate_config(raw)
        assert warnings == []

    def test_driftcheck_section_valid(self):
        """[driftcheck] section with valid keys should pass."""
        raw = {
            "driftcheck": {
                "ignore_patterns": ["*.log"],
            }
        }
        warnings = validate_config(raw)
        assert warnings == []

    def test_driftcheck_section_with_unknown_key(self):
        """Unknown key inside [driftcheck] section should warn."""
        raw = {
            "driftcheck": {
                "unknown_key": "value",
            }
        }
        warnings = validate_config(raw, strict=False)
        assert len(warnings) == 1
        assert "unknown_key" in warnings[0]

    def test_driftcheck_section_unknown_key_strict(self):
        """Unknown key inside [driftcheck] section should raise in strict mode."""
        raw = {
            "driftcheck": {
                "unknown_key": "value",
            }
        }
        with pytest.raises(ConfigValidationError, match="unknown_key"):
            validate_config(raw, strict=True)


class TestLoadConfigWithValidation:
    """Tests for load_config() with validation."""

    def test_valid_toml_no_warnings(self, tmp_path):
        """Valid .driftcheck.toml should load without warnings."""
        toml_file = tmp_path / ".driftcheck.toml"
        toml_file.write_text("""
[driftcheck]
ignore_patterns = ["*.log", "node_modules/*"]
fail_on_informational = true
""")
        cfg = load_config(tmp_path)
        assert cfg["ignore_patterns"] == ["*.log", "node_modules/*"]
        assert cfg["fail_on_informational"] is True

    def test_typo_warns_to_stderr(self, tmp_path, capsys):
        """Typo in config key should print warning to stderr."""
        toml_file = tmp_path / ".driftcheck.toml"
        toml_file.write_text("""
[driftcheck]
ignore_paterns = ["*.log"]
""")
        cfg = load_config(tmp_path)
        captured = capsys.readouterr()
        assert "ignore_paterns" in captured.err
        assert "WARNING" in captured.err

    def test_strict_mode_raises(self, tmp_path):
        """Strict mode should raise on unknown keys."""
        toml_file = tmp_path / ".driftcheck.toml"
        toml_file.write_text("""
[driftcheck]
ignore_paterns = ["*.log"]
""")
        with pytest.raises(ConfigValidationError):
            load_config(tmp_path, strict=True)

    def test_no_config_file_uses_defaults(self, tmp_path):
        """Missing .driftcheck.toml should use defaults."""
        cfg = load_config(tmp_path)
        assert cfg == DEFAULT_CONFIG

    def test_top_level_keys_validated(self, tmp_path, capsys):
        """Top-level keys (outside [driftcheck]) should also be validated."""
        toml_file = tmp_path / ".driftcheck.toml"
        toml_file.write_text("""
ignore_paterns = ["*.log"]
""")
        load_config(tmp_path)
        captured = capsys.readouterr()
        assert "ignore_paterns" in captured.err

"""Tests for pre-commit config drift detection: .pre-commit-config.yaml rev vs README."""
from __future__ import annotations
from driftcheck.detectors.pre_commit import (
    parse_pre_commit_revs,
    find_pre_commit_drift,
)


class TestParsePreCommitRevs:
    def test_simple_single_repo(self):
        text = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.0.0
    hooks:
      - id: trailing-whitespace
"""
        result = parse_pre_commit_revs(text)
        assert result == {"https://github.com/pre-commit/pre-commit-hooks": "4.0.0"}

    def test_multiple_repos(self):
        text = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.0.0
    hooks:
      - id: trailing-whitespace
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
"""
        result = parse_pre_commit_revs(text)
        assert result == {
            "https://github.com/pre-commit/pre-commit-hooks": "4.0.0",
            "https://github.com/psf/black": "23.1.0",
        }

    def test_no_v_prefix(self):
        text = """repos:
  - repo: https://github.com/some/repo
    rev: 1.2.3
    hooks:
      - id: some-hook
"""
        result = parse_pre_commit_revs(text)
        assert result == {"https://github.com/some/repo": "1.2.3"}

    def test_empty(self):
        assert parse_pre_commit_revs("") == {}

    def test_whitespace(self):
        assert parse_pre_commit_revs("   \n  \n") == {}

    def test_missing_rev(self):
        text = """repos:
  - repo: https://github.com/some/repo
    hooks:
      - id: some-hook
"""
        result = parse_pre_commit_revs(text)
        # No rev: line means repo is not captured
        assert result == {}


class TestFindPreCommitDrift:
    def test_drift_found(self):
        text = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.0.0
    hooks:
      - id: trailing-whitespace
"""
        docs = {"README.md": "We use pre-commit 5.0.0 for linting."}
        result = find_pre_commit_drift(text, docs)
        assert len(result) == 1
        assert result[0]["doc_version"] == "5.0.0"
        assert result[0]["rev"] == "4.0.0"
        assert result[0]["repo"] == "https://github.com/pre-commit/pre-commit-hooks"

    def test_no_drift_same_major(self):
        text = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.0.0
    hooks:
      - id: trailing-whitespace
"""
        docs = {"README.md": "We use pre-commit 4.0.0 for linting."}
        result = find_pre_commit_drift(text, docs)
        assert result == []

    def test_no_drift_v_prefix_in_doc(self):
        text = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.0.0
    hooks:
      - id: trailing-whitespace
"""
        docs = {"README.md": "We use pre-commit v4.0.0 for linting."}
        result = find_pre_commit_drift(text, docs)
        assert result == []

    def test_empty_config(self):
        result = find_pre_commit_drift("", {"README.md": "pre-commit 5.0.0"})
        assert result == []

    def test_missing_config(self):
        result = find_pre_commit_drift("", {})
        assert result == []

    def test_no_readme_mention(self):
        text = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.0.0
    hooks:
      - id: trailing-whitespace
"""
        docs = {"README.md": "No mention of pre-commit here."}
        result = find_pre_commit_drift(text, docs)
        assert result == []

    def test_drift_minor_difference(self):
        """Drift is only flagged on major version difference."""
        text = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.1.0
    hooks:
      - id: trailing-whitespace
"""
        docs = {"README.md": "We use pre-commit 4.2.0 for linting."}
        result = find_pre_commit_drift(text, docs)
        # Same major version (4), no drift
        assert result == []

    def test_multiple_hooks_different_repos(self):
        text = """repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.0.0
    hooks:
      - id: trailing-whitespace
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
"""
        docs = {"README.md": "pre-commit 3.0.0 and black 23.1.0"}
        result = find_pre_commit_drift(text, docs)
        # Only pre-commit-hooks has drift (4 vs 3), black matches (23 == 23)
        assert len(result) == 1
        assert result[0]["repo"] == "https://github.com/pre-commit/pre-commit-hooks"

    def test_formatting_with_comma(self):
        """Handle rev values with trailing content (e.g., hashes, comments)."""
        text = """repos:
  - repo: https://github.com/pre-commit/some-repo
    rev: v1.0.0
    hooks:
      - id: some-hook
"""
        docs = {"README.md": "pre-commit 2.0.0"}
        result = find_pre_commit_drift(text, docs)
        assert len(result) == 1

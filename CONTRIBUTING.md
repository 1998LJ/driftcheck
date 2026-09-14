# Contributing to driftcheck

Thank you for your interest in contributing! This document outlines the process for contributing to driftcheck.

## Development Setup

1. **Clone the repo**:
   ```bash
   git clone https://github.com/yunaremaia/driftcheck.git
   cd driftcheck
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

3. **Run tests**:
   ```bash
   pytest
   ```

## Code Style

- We use `black` for formatting and `ruff` for linting
- Type hints are required for public functions
- All new detectors must include tests (see `tests/test_detectors/`)

## Adding a New Detector

1. Create a new module in `src/driftcheck/detectors/`
2. Implement `find_*_diff()` function returning `list[dict]`
3. Register in `src/driftcheck/detectors/__init__.py`
4. Add entry to `src/driftcheck/config.py` (DRIFT_KEYS)
5. Add SARIF rule in `src/driftcheck/sarif.py`
6. Add CLI info in `src/driftcheck/cli.py`
7. Add file patterns in `src/driftcheck/git_mode.py`
8. Write tests in `tests/test_detectors/`
9. Update README.md stats

See `references/driftcheck-detector-pattern.md` for the full checklist.

## Commit Messages

Follow conventional commits:
- `feat:` new feature (detector, CLI flag)
- `fix:` bug fix
- `test:` adding tests
- `docs:` documentation
- `chore:` maintenance

## Pull Request Process

1. Fork the repo and create a feature branch
2. Make your changes with tests
3. Ensure all tests pass: `pytest`
4. Update README.md if adding new features
5. Open a PR with a clear description

## Code of Conduct

Be respectful and constructive. We welcome contributors of all experience levels.

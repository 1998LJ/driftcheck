# Driftcheck Manifest — v0.1.45

## Core Stats
- **61 detector modules** (files in `src/driftcheck/detectors/` excluding `__init__.py`)
- **63 registered detectors** (imported in `src/driftcheck/detectors/__init__.py`)
- **65 total find_* functions** (including split environment detectors, lockfile variants, Nix)
- **1001 tests** with >95% code coverage
- **SARIF 2.1.0** output for GitHub Code Scanning

## Recent Commits
- `2414515` docs: correct detector counts to 62 modules, 63 registered detectors
- `43d2f86` feat: add Nix flake.lock drift detection
- `f8231a6` docs: correct detector module count to 60 (actual files in detectors/)
- `348fcb0` docs: correct detector counts to match codebase reality (61 modules, 64 registered)
- `9d9d644` docs: update detector counts after Bazel detector merge (60 modules, 64 registered)
- `9caabbf` feat: add Bazel drift detection (#73)
- `b3544a5` docs: correct detector counts to match codebase reality (59 modules, 63 registered)
- `31bca51` docs: add devcontainer and renovate detectors to README Checks section
- `4e81515` docs: correct detector counts to match codebase reality (60 modules, 66 registered, 1089 tests)

## Note on Count
There are **61 detector module files** in `src/driftcheck/detectors/` (62 Python files including `__init__.py`, which is not a detector module — it just imports them). The README previously said "62 detector modules" (commit `2414515`) but was corrected to **61 detector modules** in commit `2414515` follow-up.

## Detectors Not Listed in README "Checks" Section
The following detectors exist in `src/driftcheck/detectors/` but are NOT listed in the README "Checks" section:

| Detector | File | Notes |
|----------|------|-------|
| Actions | `actions.py` | GitHub Actions version drift |
| Bazel | `bazel.py` | Bazel version drift |
| Bun | `bun.py` | Bun version drift |
| CI OS | `ci_os.py` | Deprecated GitHub Actions runners |
| CircleCI | `circleci.py` | CircleCI image drift |
| CMake | `cmake.py` | CMake version drift |
| Compose | `compose.py` | Docker Compose image drift |
| Conda | `conda.py` | Conda environment drift |
| Count | `count.py` | Skills count drift |
| Dart | `dart.py` | Dart/Flutter SDK drift |
| Deno | `deno.py` | Deno version drift |
| Dependabot | `dependabot.py` | Dependabot coverage drift |
| Docker Bases | `docker_bases.py` | Dockerfile base image drift |
| Docker Multistage | `docker_multistage.py` | Multistage Dockerfile drift |
| EditorConfig | `editorconfig.py` | EditorConfig drift |
| Elixir | `elixir.py` | Elixir version drift |
| Engines | `engines.py` | Engines drift |
| Env Drift | `env_drift.py` | Environment file drift |
| External | `external.py` | External resource drift |
| GitLab CI | `gitlab.py` | GitLab CI image drift |
| Git Tag | `git_tag.py` | Git tag vs README drift |
| Go | `go.py` | Go version drift |
| Gradle Catalog | `gradle_catalog.py` | Gradle catalog drift |
| Helm | `helm.py` | Helm chart drift |
| Java | `java.py` | Java version drift |
| Jenkins | `jenkins.py` | Jenkins tool drift |
| K8s | `k8s.py` | Kubernetes manifest drift |
| Kotlin | `kotlin.py` | Kotlin version drift |
| Line Endings | `lineending.py` | Line ending drift |
| Lockfile | `lockfile.py` | Lockfile presence drift |
| Makefile | `makefile.py` | Makefile tool drift |
| Maven | `maven.py` | Maven version drift |
| Mise | `mise.py` | Mise tool drift |
| Nix | `nix.py` | Nix flake.lock drift |
| NPMRC | `npmrc.py` | NPMRC registry drift |
| NVMRC | `nvmrc.py` | NVMRC version drift |
| Package Manager | `package_manager.py` | Package manager drift |
| PHP | `php.py` | PHP version drift |
| Pipfile | `pipfile.py` | Pipfile lock drift |
| PNPM | `pnpm.py` | PNPM lock drift |
| Poetry | `poetry.py` | Poetry lock drift |
| Python | `python.py` | Python version drift |
| Python Version | `python_version.py` | Python version file drift |
| Requirements | `requirements.py` | Requirements drift |
| Ruby | `ruby.py` | Ruby version drift |
| Rust | `rust.py` | Rust toolchain drift |
| Swift | `swift.py` | Swift version drift |
| Taskfile | `taskfile.py` | Taskfile drift |
| Terraform | `terraform.py` | Terraform provider drift |
| Tool Versions | `tool_versions.py` | Tool versions drift |
| Typosquat | `typosquat.py` | Typosquat drift |
| Version Files | `version_files.py` | Version file drift |
| VSCode | `vscode.py` | VSCode extension drift |
| Yarn RC | `yarnrc.py` | Yarn RC drift |
| Pre-commit | `pre_commit.py` | Pre-commit rev drift |
| Devcontainer | `devcontainer.py` | Devcontainer image drift |
| Renovate | `renovate.py` | Renovate config drift |


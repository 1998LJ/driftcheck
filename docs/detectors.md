# Detectors

driftcheck ships **58 detector modules** covering **61 independent detectors**. Each checks for a specific kind of version drift between toolchain files and documentation.

## Language Runtimes

| Detector | Description |
|----------|-------------|
| `rust_drifts` | `rust-toolchain.toml` `channel` and `Cargo.toml` `rust-version` vs README. Minor-aware (patch differences ignored). |
| `node_drifts` | `package.json` `engines.node` vs README. |
| `deno_drifts` | `deno.json`/`deno.jsonc` `version` or `deno` field vs README Deno mentions. Major.minor comparison. |
| `bun_drifts` | `package.json` `engines.bun` vs README. Major.minor comparison. |
| `python_drifts` | `pyproject.toml` `requires-python` vs README. |
| `go_drifts` | `go.mod` `go` directive vs README. |
| `php_drifts` | `composer.json` `require.php` vs README. Major.minor comparison. |
| `ruby_drifts` | `Gemfile` `ruby "x.y.z"` vs README. Major.minor comparison. |
| `dotnet_drifts` | `*.csproj` `<TargetFramework>` vs README. Handles multi-targeting. |
| `elixir_drifts` | `mix.exs` `elixir:` version vs README. |
| `kotlin_drifts` | `build.gradle.kts` plugin version vs README. |
| `swift_drifts` | `Package.swift` `swift-tools-version` and dependency pins vs README. |
| `dart_drifts` | `pubspec.yaml` `environment.sdk` constraint vs README. |

## Package Managers & Lockfiles

| Detector | Description |
|----------|-------------|
| `pipfile_drifts` | `Pipfile` vs `Pipfile.lock` version mismatches. |
| `requirements_drifts` | Package versions in `requirements.txt` vs dependency tables in `pyproject.toml` and README mentions. Major.minor comparison. |
| `poetry_drifts` | Python and package versions in `pyproject.toml` Poetry dependency sections vs README. Major.minor comparison. |
| `conda_drifts` | `environment.yml` unpinned packages. |
| `gradle_catalog_drifts` | `libs.versions.toml` (Gradle version catalog) vs README. |
| `lockfile_drifts` | Missing, stale, or orphaned lockfiles (informational). |
| `npmrc_drifts` | `.npmrc` registry vs README mentions. |
| `yarnrc_drifts` | `.yarnrc.yml` Yarn version vs README mentions. |
| `pnpm_workspace_drifts` | `pnpm-workspace.yaml` packages vs `package.json` workspaces. |
| `package_manager_drifts` | `package.json` `packageManager` name vs the package manager identified by an existing lockfile. |
| `engines_drifts` | `package.json` `engines.node` vs `.nvmrc` and `volta.node`. Major.minor comparison. |

## CI/CD

| Detector | Description |
|----------|-------------|
| `actions_drifts` | Outdated `uses: action@version` for 18 popular actions. Detects deprecated Node 20 runtime. |
| `gh_actions_version_drifts` | Outdated GitHub Actions versions by category. |
| `gitlab_drifts` | `.gitlab-ci.yml` image tags vs README. |
| `circleci_drifts` | `.circleci/config.yml` docker image tags vs README. |
| `jenkins_drifts` | `Jenkinsfile` tool versions (`nodejs`, `python`, `docker.image`) vs README. |
| `ci_os_drifts` | Deprecated GitHub Actions runners (ubuntu-18.04, macos-11, windows-2016). |
| `pre_commit_drifts` | `.pre-commit-config.yaml` revisions for repository URLs containing `pre-commit` vs README `pre-commit` versions. Major-version comparison. |

## Infrastructure

| Detector | Description |
|----------|-------------|
| `docker_drifts` | `Dockerfile` `FROM <image>:<tag>` vs README. |
| `docker_bases_drifts` | Missing or floating `FROM` tags and differing tags for the same base image across Dockerfiles or stages. |
| `docker_multistage_drifts` | Conflicting versions of the same image across `FROM` stages, ignoring tag variants such as `-alpine`. Also compares the final stage image tag with README. |
| `devcontainer_drifts` | `devcontainer.json` numeric image tags and version values for features with hyphenated short names (such as `docker-in-docker`) vs README mentions. |
| `dc_drifts` | `docker-compose.yml`/`compose.yaml` image tags vs README. |
| `k8s_drifts` | Kubernetes manifest image tags vs README. |
| `helm_drifts` | `Chart.yaml`/`values.yaml` image tags vs README. |
| `terraform_drifts` | `versions.tf` `required_providers` `version` vs README. |
| `env_drifts` | Combined results from `env_example_drifts`, `compose_override_drifts`, and `helm_values_drifts` below. |
| `env_example_drifts` | `.env.example` vs `.env` for missing or extra keys. Also reports a missing `.env` file. |
| `compose_override_drifts` | Image tags in base Compose files (`docker-compose.yml`/`.yaml`, `compose.yml`/`.yaml`) vs environment override files such as `docker-compose.prod.yml`. |
| `helm_values_drifts` | `values.yaml` (root or a chart directory) vs environment-specific values files for differing `replicaCount`, `tag`, `repository`, and scalar `resources` values. |

## Build Tools

| Detector | Description |
|----------|-------------|
| `makefile_drifts` | Makefile tool version variables (`GCC_VERSION`, `CMAKE_VERSION`, `GO_VERSION`). |
| `cmake_drifts` | `CMakeLists.txt` `cmake_minimum_required` version vs README. |
| `maven_drifts` | `pom.xml` `java.version`, `maven.compiler.source/target` vs README. |
| `java_drifts` | `build.gradle` `sourceCompatibility`, `jvmTarget` vs README. |
| `taskfile_drifts` | `Taskfile.yml` tool version variables vs README. |

## Configuration

| Detector | Description |
|----------|-------------|
| `tool_versions_drifts` | `.tool-versions` (asdf/mise) — Node, Python, Go, Rust, Ruby, Java, PHP, .NET. |
| `mise_drifts` | `mise.toml` `[tools]` section vs README. |
| `editorconfig_drifts` | `.editorconfig` indent size, indent style, and line endings vs README, plus indent size vs `tabSize` in `.vscode/settings.json`. |
| `vscode_ext_drifts` | README extension recommendations missing from the nonempty `recommendations` list in `.vscode/extensions.json`. |
| `ruby_version_drifts`, `python_version_drifts`, `node_version_drifts`, `java_version_drifts`, `terraform_version_drifts` | Version-file checks using `.ruby-version`, `.python-version`, `.node-version`, `.java-version`, and `.terraform-version` vs README. |
| `nvmrc_drifts` | `.nvmrc` vs `package.json` engines.node (informational). |
| `dependabot_drifts` | Ecosystems used but not covered by `.github/dependabot.yml` (informational). |
| `git_tag_drifts` | Latest git tag vs README version mentions. |

## Other

| Detector | Description |
|----------|-------------|
| `lineending_drifts` | Missing `* text=auto eol=lf` in `.gitattributes` (informational). |
| `external_resource_drifts` | Third-party CDN dependencies that break offline rendering (informational). |
| `typosquat_drifts` | Names from Python manifests (`requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py`), `package.json`, and `Cargo.toml` vs bundled known-package lists. Flags similar names as possible typosquats (informational). |
| `count_drifts` | `skills/` directory count vs README mentions of "N skills". |
| `plugin_<name>_drifts` | Custom drift detection via plugins. |

## Detector Aliases

Many detectors can be referenced by short name in `--only`/`--exclude`:

```bash
driftcheck --only rust,node,python,go
driftcheck --exclude lockfile,nvmrc,ci_os
```

The short name is the detector's `kind` prefix (before `_drifts`).

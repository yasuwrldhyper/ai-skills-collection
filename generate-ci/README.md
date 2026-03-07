# generate-ci

Interactive GitHub Actions CI workflow generator skill for Claude Code.

## Overview

`/generate-ci` automatically detects your project's language and infrastructure,
then interactively generates GitHub Actions CI workflows following security and
quality best practices. It produces production-ready YAML files with SHA-pinned
Actions, minimal token permissions, coverage visualization, and secret scanning
integrated from the start.

## Usage

```text
/generate-ci [project-path]
```

**Examples:**

```sh
# Run in the current directory
/generate-ci

# Target a specific project subdirectory
/generate-ci generate-ci/sample/python/

# Target a TypeScript project
/generate-ci ./my-app
```

## What Gets Generated

| File | Contents |
| --- | --- |
| `.github/workflows/ci.yml` | Lint + Test with coverage + Build + actionlint |
| `.github/workflows/security.yml` | Secret scanning (gitleaks) + SAST + Dependency audit |
| `.github/workflows/terraform.yml` | Terraform fmt / validate / tflint (only for Terraform projects) |
| `renovate.json` OR `.github/dependabot.yml` | Dependency update automation (your choice) |

## Supported Languages & Tools

| Language | Package Manager | Lint | Test | Coverage |
| --- | --- | --- | --- | --- |
| Python | uv / pip / poetry | Ruff | pytest | pytest-cov (full src coverage) |
| TypeScript/Node.js | npm / yarn / pnpm | Biome / ESLint | Vitest / Jest | v8/istanbul (full src coverage) |
| Terraform (IaC) | - | tflint | terraform validate | - |

## CI Best Practices Applied

- **SHA-pinned Actions** — all third-party actions are pinned to a full commit SHA for supply chain security
- **Minimal GITHUB_TOKEN permissions** — each job declares only the permissions it needs
- **Coverage includes untested files** — `src/`-wide measurement (not just tested files), catching zero-coverage modules
- **PR coverage comments** — coverage delta is posted directly on pull requests
- **GitHub Annotations** — lint errors appear as inline PR annotations
- **Security tab integration** — SARIF upload pushes security results into the GitHub Security tab
- **`concurrency: cancel-in-progress`** — stale runs for the same PR/branch are cancelled automatically
- **`timeout-minutes`** — every job has a timeout to prevent runaway builds consuming minutes
- **Dependency update automation** — Actions version bumps are covered by Renovate / Dependabot
- **Out-of-date Actions check** — `actionlint` flags deprecated or unpinned action references
- **Secret scanning** — gitleaks scans every push and PR for accidentally committed secrets

## Interactive Configuration

During `/generate-ci`, Claude will ask a series of questions to tailor the output:

1. **Confirm detected language / package manager** — Claude auto-detects from `pyproject.toml`, `package.json`, `*.tf`, etc.
2. **Select CI steps to include** — choose which checks to enable (lint, test, build, security, …)
3. **Workflow split** — generate separate `ci.yml` + `security.yml`, or merge into a single file
4. **Dependency management tool** — Renovate (`renovate.json`) or Dependabot (`.github/dependabot.yml`)
5. **Repository visibility** — Public (SARIF upload available) or Private (alternative reporting)
6. **Security scan failure policy** — Strict (block merge) / Advisory (annotate only) / Log-only

## Sample Projects

`sample/` contains minimal demo projects you can use to test the skill end-to-end:

| Directory | Description |
| --- | --- |
| `sample/python/` | Python project managed with uv, includes intentional coverage gaps |
| `sample/typescript/` | TypeScript project (npm + Vitest) with partial test coverage |
| `sample/terraform/` | AWS S3 Terraform module with tflint configuration |

**Try it:**

```sh
/generate-ci generate-ci/sample/python/
```

## Skill Security Notes

- All generated Actions use **SHA pinning** with an inline version comment for readability:

  ```yaml
  uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
  ```

- **Dependabot / Renovate** automatically open PRs when new SHA mappings are published, keeping pins fresh without manual effort.
- **GITHUB_TOKEN permissions** are declared at the job level with the least privilege required; write access is never granted globally.

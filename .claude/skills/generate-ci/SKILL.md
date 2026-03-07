---
name: generate-ci
description: Interactively generates GitHub Actions CI workflow files based on project language detection. Supports Python, TypeScript/Node.js, and Terraform. Produces best-practice workflows with SHA-pinned actions, minimal GITHUB_TOKEN permissions, full-source coverage reporting, secret scanning, and dependency management automation.
argument-hint: [project-path] (defaults to current directory)
allowed-tools: Read, Glob, Grep, Write, Bash
---

# /generate-ci Skill

Generate GitHub Actions CI workflow files for the project at `$ARGUMENTS` (or current directory if not specified).

Follow each phase sequentially. Ask the user for confirmation before generating files.

---

## Phase 1: Project Auto-Detection

Use Glob and Read tools to detect the project's language, package manager, and existing CI setup.

### 1-1. Detect project root

Set `PROJECT_ROOT` to `$ARGUMENTS` if provided, otherwise use the current working directory.

### 1-2. Language and tool detection

Check for the following files under `PROJECT_ROOT`:

| File pattern | Detected stack |
| --- | --- |
| `pyproject.toml` | Python |
| `requirements.txt` or `setup.py` | Python |
| `package.json` + `tsconfig.json` | TypeScript |
| `package.json` (no tsconfig) | Node.js |
| `*.tf` or `**/*.tf` | Terraform |
| `mise.toml` | Read for tool versions |

For Python, also check:

- `uv.lock` → package manager is **uv**
- `poetry.lock` → package manager is **poetry**
- neither → assume **pip**

For Node.js/TypeScript, also check:

- `yarn.lock` → package manager is **yarn**
- `pnpm-lock.yaml` → package manager is **pnpm**
- `package-lock.json` → package manager is **npm**

For Python test framework, check `pyproject.toml` for `[tool.pytest]` or `[tool.pytest.ini_options]` → **pytest**. Otherwise assume **pytest** as default.

For Node.js/TypeScript test framework, read `package.json` scripts and devDependencies:

- `vitest` → **Vitest**
- `jest` → **Jest**
- default → **Vitest** (recommended)

For Node.js/TypeScript linter:

- `biome.json` or `@biomejs/biome` in devDependencies → **Biome**
- `eslint` in devDependencies → **ESLint**
- default → **Biome** (recommended)

### 1-3. Detect source directories

For Python: look for `src/` directory or check `[tool.coverage.run] source` in `pyproject.toml`.
For TypeScript: look for `src/` directory or check `tsconfig.json` `rootDir`.

### 1-4. Check existing CI

Use Glob to check if `.github/workflows/` exists and list any existing workflow files.

### 1-5. Report detection summary

Present the detection summary to the user in this format:

```text
Detected project configuration:
  Language(s):       Python + Terraform  (or whatever was found)
  Package manager:   uv
  Test framework:    pytest
  Linter:            Ruff
  Source directory:  src/
  Terraform:         Yes (*.tf files found)
  Existing CI:       None (or list existing files)

Is this correct? (yes / describe corrections)
```

Wait for user confirmation before proceeding to Phase 2.

---

## Phase 2: Interactive CI Configuration

Ask the user a series of questions to configure the CI. Ask them together in a single message.

```text
Please answer the following to configure your CI:

1. Which CI steps do you want? (default: all)
   - [x] Lint / Format check
   - [x] Test with coverage (PR comment)
   - [x] Build verification
   - [x] Secret scanning (gitleaks)
   - [x] SAST (CodeQL + Trivy)
   - [x] Dependency audit
   - [x] Actions out-of-date check (actionlint)
   - [x] Conventional Commits / PR title check
   Uncheck any you don't need.

2. Workflow file structure:
   a) Separate files: ci.yml + security.yml [recommended]
   b) Single file: ci.yml (all steps)
   (For Terraform: always generates terraform.yml separately)

3. Dependency management automation:
   a) Renovate (renovate.json) [recommended - more flexible]
   b) Dependabot (.github/dependabot.yml) [GitHub native]
   c) Skip

4. Repository visibility:
   a) Private / internal [default]
   b) Public (enables fork PR support with restricted permissions)

5. Security scan failure policy:
   a) Advisory - only CRITICAL findings block CI [recommended for new projects]
   b) Strict - any finding blocks CI
   c) Log-only - results visible but never block CI
```

Wait for user responses before proceeding to Phase 3.

---

## Phase 3: File Generation

Based on Phase 1 detection and Phase 2 answers, generate the workflow files using the Write tool.

**Important security rules for ALL generated workflows:**

- Pin ALL third-party Actions to their git SHA hash, with a version comment
- Specify `permissions:` on each job individually (never at workflow level alone)
- Always include `concurrency: cancel-in-progress: true`
- Always include `timeout-minutes` on every job
- Use `hashFiles()` in all cache keys

Use the templates below, substituting detected values.

---

## Templates

### Template: ci.yml (Python + uv)

```yaml
# .github/workflows/ci.yml
# Actions versions are pinned to SHA for security.
# Dependabot/Renovate will keep them up to date automatically.

name: CI

on:
  pull_request:
  push:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    name: Lint & Format
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - uses: astral-sh/setup-uv@f0ec1fc3b38f5e7cd731bb6ce540c5af426746bb  # v5.4.0
        with:
          enable-cache: true
          cache-dependency-glob: uv.lock
      - name: Lint with Ruff
        run: uv run ruff check --output-format=github .
      - name: Format check with Ruff
        run: uv run ruff format --check .

  test:
    name: Test & Coverage
    runs-on: ubuntu-latest
    timeout-minutes: 15
    permissions:
      contents: read
      pull-requests: write  # Required for PR coverage comment
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - uses: astral-sh/setup-uv@f0ec1fc3b38f5e7cd731bb6ce540c5af426746bb  # v5.4.0
        with:
          enable-cache: true
          cache-dependency-glob: uv.lock
      - name: Install dependencies
        run: uv sync --all-extras
      # NOTE: --cov=src measures ALL files in src/, including untested ones (shown as 0%)
      # This gives an honest picture of total coverage. Adjust --cov=<your-src-dir> if needed.
      - name: Run tests with coverage
        run: |
          uv run pytest \
            --cov=src \
            --cov-branch \
            --cov-report=xml:coverage.xml \
            --cov-report=term-missing \
            --junitxml=test-results.xml
        # Retry on failure to handle flaky tests (remove if tests are stable)
        # To enable retries: uv add pytest-rerunfailures --dev
        # then add: --reruns 2 --reruns-delay 5
      - name: Upload coverage report
        uses: actions/upload-artifact@6f51ac03b9356f520e9adb1b1b7802705f340c2b  # v4.5.0
        if: always()
        with:
          name: coverage-report
          path: coverage.xml
          retention-days: 7
      - name: Post coverage comment on PR
        if: github.event_name == 'pull_request'
        uses: MishaKav/pytest-coverage-comment@81882822c5cd55bc8e856418ecb60c5c45c11247  # v1.1.52
        with:
          pytest-xml-coverage-path: coverage.xml
          junitxml-path: test-results.xml

  build:
    name: Build
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - uses: astral-sh/setup-uv@f0ec1fc3b38f5e7cd731bb6ce540c5af426746bb  # v5.4.0
        with:
          enable-cache: true
          cache-dependency-glob: uv.lock
      - name: Build package
        run: uv build

  actionlint:
    name: Lint GitHub Actions workflows
    runs-on: ubuntu-latest
    timeout-minutes: 5
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - name: Run actionlint
        uses: raven-actions/actionlint@3a10a4f81f7bb6af5be900e2e6b0c9c1a94cc428  # v2.0.0
```

---

### Template: ci.yml (Python + pip)

Same as uv variant but replace setup steps with:

```yaml
      - uses: actions/setup-python@0b93645bdc8f3c7c6f8d3cf81c2a3a0e5e68a3a3  # v5.3.0
        with:
          python-version: "3.12"
          cache: pip
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=src --cov-branch --cov-report=xml --junitxml=test-results.xml
```

---

### Template: ci.yml (TypeScript + npm + Biome)

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
  push:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  lint:
    name: Lint & Format
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - uses: actions/setup-node@cdca7365b2dadb8aad0a33bc7601856ffabcc48e  # v4.3.0
        with:
          node-version-file: .nvmrc  # or: node-version: "22"
          cache: npm
      - run: npm ci
      - name: Lint with Biome
        run: npx biome check --reporter=github .
      # Biome annotations appear inline in PR diffs

  test:
    name: Test & Coverage
    runs-on: ubuntu-latest
    timeout-minutes: 15
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - uses: actions/setup-node@cdca7365b2dadb8aad0a33bc7601856ffabcc48e  # v4.3.0
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci
      # NOTE: vitest.config.ts must set coverage.include to cover ALL src files,
      # including untested ones. Example: include: ['src/**/*.ts']
      - name: Run tests with coverage
        run: npm test
      - name: Upload coverage
        uses: actions/upload-artifact@6f51ac03b9356f520e9adb1b1b7802705f340c2b  # v4.5.0
        if: always()
        with:
          name: coverage-report
          path: coverage/
          retention-days: 7
      - name: Post coverage report on PR
        if: github.event_name == 'pull_request'
        uses: davelosert/vitest-coverage-report-action@2500dafcee7dd64f85ab689c0b83798a8359770e  # v2.9.3
        # Note: this action is maintained by a GitHub employee; actively maintained as of 2025

  build:
    name: Build
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - uses: actions/setup-node@cdca7365b2dadb8aad0a33bc7601856ffabcc48e  # v4.3.0
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci
      - run: npm run build

  actionlint:
    name: Lint GitHub Actions workflows
    runs-on: ubuntu-latest
    timeout-minutes: 5
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - uses: raven-actions/actionlint@3a10a4f81f7bb6af5be900e2e6b0c9c1a94cc428  # v2.0.0
```

---

### Template: ci.yml (TypeScript + npm + ESLint)

Replace the lint job from the Biome template with:

```yaml
  lint:
    name: Lint
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      contents: read
      pull-requests: write  # for reviewdog PR review comments
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - uses: actions/setup-node@cdca7365b2dadb8aad0a33bc7601856ffabcc48e  # v4.3.0
        with:
          node-version-file: .nvmrc
          cache: npm
      - run: npm ci
      - uses: reviewdog/action-eslint@b19663f0faf1d4b0f1e9f92821f530a836b4b317  # v1.34.0
        with:
          reporter: github-pr-review  # posts inline review comments on PR
          eslint_flags: "src/"
```

---

### Template: security.yml

```yaml
# .github/workflows/security.yml
# Runs on PR, push to main, and daily schedule to catch newly disclosed CVEs.
name: Security

on:
  pull_request:
  push:
    branches: [main]
  schedule:
    - cron: "0 2 * * *"  # Daily at 02:00 UTC
  workflow_dispatch:

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  secret-scan:
    name: Secret Scanning
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
        with:
          fetch-depth: 0  # full history for secret scanning
      - name: Run gitleaks
        uses: gitleaks/gitleaks-action@ff98106e4c7b2bc287b24eaf42907196329070c3  # v2.3.9
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}  # remove if using Community license

  dependency-audit:
    name: Dependency Audit
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      # --- Python (uv) ---
      # - uses: astral-sh/setup-uv@f0ec1fc3b38f5e7cd731bb6ce540c5af426746bb  # v5.4.0
      # - run: uv sync && uv run pip-audit
      # --- Node.js ---
      # - uses: actions/setup-node@cdca7365b2dadb8aad0a33bc7601856ffabcc48e  # v4.3.0
      #   with: { node-version-file: .nvmrc, cache: npm }
      # - run: npm ci && npm audit --audit-level=high
      # (Uncomment the block matching your language)

  sast:
    name: SAST (CodeQL)
    runs-on: ubuntu-latest
    timeout-minutes: 30
    permissions:
      contents: read
      security-events: write  # Required for SARIF upload to Security tab
    strategy:
      fail-fast: false
      matrix:
        # Set to detected language(s): python, javascript, typescript
        language: [python]
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - name: Initialize CodeQL
        uses: github/codeql-action/init@45ef7ffa9d96ffa67d0064b2ef91fb6b2e0bf0e2  # v3.28.13
        with:
          languages: ${{ matrix.language }}
          # Security scan failure policy: ADVISORY (only critical/high alerts are errors)
          # Change to 'error' for STRICT mode (any alert = CI failure)
          # Change to 'none' for LOG-ONLY mode
          queries: security-extended
      - name: Autobuild
        uses: github/codeql-action/autobuild@45ef7ffa9d96ffa67d0064b2ef91fb6b2e0bf0e2  # v3.28.13
      - name: Analyze
        uses: github/codeql-action/analyze@45ef7ffa9d96ffa67d0064b2ef91fb6b2e0bf0e2  # v3.28.13
        with:
          category: "/language:${{ matrix.language }}"

  trivy:
    name: Trivy FS Scan
    runs-on: ubuntu-latest
    timeout-minutes: 15
    permissions:
      contents: read
      security-events: write  # Required for SARIF upload
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - name: Run Trivy
        uses: aquasecurity/trivy-action@6e7b7d1fd3e4fef0c5fa8cce1229c54b2c9bd0d8  # v0.29.0
        with:
          scan-type: fs
          format: sarif
          output: trivy-results.sarif
          # ADVISORY policy: only CRITICAL and HIGH
          severity: "CRITICAL,HIGH"
          # For STRICT: exit-code: '1' (below)
          # For LOG-ONLY: remove exit-code line
          exit-code: "0"  # change to '1' for STRICT mode
      - name: Upload Trivy results to Security tab
        uses: github/codeql-action/upload-sarif@45ef7ffa9d96ffa67d0064b2ef91fb6b2e0bf0e2  # v3.28.13
        if: always()
        with:
          sarif_file: trivy-results.sarif

  pr-title:
    name: PR Title (Conventional Commits)
    runs-on: ubuntu-latest
    timeout-minutes: 5
    if: github.event_name == 'pull_request'
    permissions:
      pull-requests: read
    steps:
      - uses: amannn/action-semantic-pull-request@0723387faaf9b38adef4775cd42cfd5155ed6017  # v5.5.3
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

### Template: terraform.yml

```yaml
# .github/workflows/terraform.yml
name: Terraform

on:
  pull_request:
    paths:
      - "**.tf"
      - "**/.tflint.hcl"
  push:
    branches: [main]
    paths:
      - "**.tf"

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  terraform-check:
    name: Terraform Lint & Validate
    runs-on: ubuntu-latest
    timeout-minutes: 15
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2

      - uses: hashicorp/setup-terraform@b9cd54a3c349d3f38e8881555d616ced269ef065  # v3.1.2

      - name: Terraform Format Check
        run: terraform fmt -check -recursive
        # If this fails: run `terraform fmt -recursive` locally and commit

      - name: Terraform Init
        run: terraform init -backend=false

      - name: Terraform Validate
        run: terraform validate

      - uses: actions/cache@5a3ec84eff668545956fd18022155c47e93e2684  # v4.2.3
        with:
          path: ~/.tflint.d/plugins
          key: tflint-${{ runner.os }}-${{ hashFiles('.tflint.hcl') }}

      - uses: terraform-linters/setup-tflint@90f42f91df18aa9e2b5a2da49e94e7e5a82e3b8d  # v4.1.1

      - name: Init tflint
        run: tflint --init

      - name: Run tflint
        run: tflint --recursive --format compact

  terraform-security:
    name: Terraform Security Scan
    runs-on: ubuntu-latest
    timeout-minutes: 15
    permissions:
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - name: Run Trivy for IaC
        uses: aquasecurity/trivy-action@6e7b7d1fd3e4fef0c5fa8cce1229c54b2c9bd0d8  # v0.29.0
        with:
          scan-type: config
          format: sarif
          output: trivy-iac.sarif
          severity: "CRITICAL,HIGH"
          exit-code: "0"
      - name: Upload results to Security tab
        uses: github/codeql-action/upload-sarif@45ef7ffa9d96ffa67d0064b2ef91fb6b2e0bf0e2  # v3.28.13
        if: always()
        with:
          sarif_file: trivy-iac.sarif
```

---

### Template: renovate.json

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended",
    ":semanticCommits",
    "group:allNonMajor",
    "schedule:weekly"
  ],
  "labels": ["dependencies"],
  "vulnerabilityAlerts": {
    "enabled": true,
    "labels": ["security", "dependencies"]
  },
  "packageRules": [
    {
      "matchManagers": ["github-actions"],
      "pinDigests": true,
      "automerge": false,
      "labels": ["dependencies", "github-actions"]
    }
  ]
}
```

---

### Template: .github/dependabot.yml

```yaml
# .github/dependabot.yml
# Dependabot keeps Actions SHA-pinned versions up to date automatically.
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
      time: "04:00"
    labels:
      - "dependencies"
      - "github-actions"
    # Keeps all Actions in .github/workflows/ up to date

  # Python (uv) - uncomment if applicable
  # - package-ecosystem: "pip"
  #   directory: "/"
  #   schedule:
  #     interval: "weekly"
  #   labels:
  #     - "dependencies"

  # Node.js / TypeScript - uncomment if applicable
  # - package-ecosystem: "npm"
  #   directory: "/"
  #   schedule:
  #     interval: "weekly"
  #   labels:
  #     - "dependencies"
```

---

## Phase 3 Execution Instructions

### Step 1: Determine files to generate

Based on Phase 2 choices, decide which files to create:

| Condition | Files to generate |
| --- | --- |
| Python detected | `ci.yml` (Python variant) |
| TypeScript detected | `ci.yml` (TypeScript variant) |
| Terraform detected | `terraform.yml` |
| Security steps selected | `security.yml` |
| Renovate selected | `renovate.json` |
| Dependabot selected | `.github/dependabot.yml` |

If both Python and TypeScript are detected in the same project, generate a combined `ci.yml` with separate jobs for each language.

### Step 2: Customize templates

Before writing files, substitute these values from Phase 1 detection:

- Package manager commands (`uv run`, `pip`, `npm ci`, `yarn`, `pnpm install`)
- Source directory in `--cov=<src_dir>` and `coverage.include`
- Python version from `mise.toml` or `pyproject.toml` requires-python
- Node.js version from `.nvmrc`, `mise.toml`, or `package.json` `engines.node`
- CodeQL language (`python`, `javascript`, `typescript`)
- If repository is **Public**, add this to fork PR-sensitive jobs (coverage comment):

  ```yaml
  # Restrict on fork PRs (no write permissions available from forks)
  if: github.event.pull_request.head.repo.full_name == github.repository
  ```

### Step 3: Apply security failure policy from Phase 2

**Advisory (default):**

- CodeQL: keep `queries: security-extended` (alerts appear in Security tab but don't block)
- Trivy: `exit-code: "0"`, `severity: "CRITICAL,HIGH"`

**Strict:**

- CodeQL: use `queries: security-and-quality`
- Trivy: `exit-code: "1"`, `severity: "CRITICAL,HIGH,MEDIUM"`

**Log-only:**

- CodeQL: `queries: security-extended`, no additional flags
- Trivy: `exit-code: "0"`, `severity: "CRITICAL,HIGH,MEDIUM,LOW"`

### Step 4: Check for existing workflows

If `.github/workflows/` already contains files, warn the user:

```text
⚠️  Existing workflow files found: ci.yml
    Overwrite? (yes / no / rename to ci-new.yml)
```

Wait for confirmation before writing.

### Step 5: Write files

Use the Write tool to create each file. Use the absolute path resolved from `PROJECT_ROOT`.
Create the `.github/workflows/` directory if it does not exist.

### Step 6: Summary

After writing all files, display a summary:

```text
✅ Generated files:
   .github/workflows/ci.yml       — Lint + Test (coverage PR comment) + Build + actionlint
   .github/workflows/security.yml — Secret scan + CodeQL + Trivy + PR title check
   .github/workflows/terraform.yml — fmt + validate + tflint + Trivy IaC scan
   renovate.json                  — Weekly dep updates with SHA pinning for Actions

⚠️  Action SHA versions:
   All Actions are pinned to SHA with version comments (e.g., # v4.2.2).
   Run /generate-ci again or use Renovate/Dependabot to keep them current.

📋 Recommended next steps:
   1. Review generated files and adjust source directory paths if needed
   2. Commit and push to trigger CI (push to main or open a PR)
   3. If using Renovate: install the Renovate GitHub App
   4. If using Dependabot: no extra setup needed, it's GitHub native
   5. For gitleaks Community license: GITLEAKS_LICENSE secret is optional
   6. Check the GitHub Security tab after first security.yml run
```

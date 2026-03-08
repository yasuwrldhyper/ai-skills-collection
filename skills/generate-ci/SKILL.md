---
name: generate-ci
description: Interactively generates GitHub Actions CI workflow files based on project language detection. Supports Python, TypeScript/Node.js, and Terraform. Produces best-practice workflows with SHA-pinned actions, minimal GITHUB_TOKEN permissions, full-source coverage reporting, secret scanning, and dependency management automation.
argument-hint: [project-path] (defaults to current directory)
allowed-tools: Read, Glob, Grep, Write, Bash, AskUserQuestion
---

# /generate-ci Skill

Generate GitHub Actions CI workflow files for the project at `$ARGUMENTS` (or current directory if not specified).

Follow each phase sequentially. Ask the user for confirmation before generating files.

---

## Phase 1: Project Auto-Detection

> **Scope limitation**: This skill targets single-package repositories.
> Monorepos (multiple `package.json` / `pyproject.toml` at different directory levels,
> or workspaces configured in `package.json`) are **not supported**.
> If a monorepo is detected, inform the user and stop — do not attempt to generate CI files.

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
- If `package.json` exists but **no lockfile** is present, inform the user:
  "⚠️ No lockfile detected (package-lock.json, yarn.lock, or pnpm-lock.yaml).
  The generated workflow uses `npm ci` / `yarn --frozen-lockfile` which requires a committed lockfile.
  Please run `npm install` / `yarn install` / `pnpm install` and commit the lockfile, then re-run /generate-ci."
  Stop generation and do not proceed to Phase 2.

For Python linter, check `pyproject.toml`:

- `[tool.ruff]` section present → **Ruff**
- default → **Ruff** (recommended)

For Python version, check in order:

- `mise.toml` `[tools] python = "X.Y"` → use that version
- `pyproject.toml` `[project] requires-python = ">=X.Y"` → use that minimum version
- Neither found → default to `"3.12"`

For Python test framework, check `pyproject.toml` for `[tool.pytest]` or `[tool.pytest.ini_options]` → **pytest**. Otherwise assume **pytest** as default.

For Python pytest configuration, check `pyproject.toml` `[tool.pytest.ini_options]`:

- If `addopts` contains coverage-related flags (`--cov`, `--cov-report`, etc.), the project already configures coverage.
  In this case, the generated workflow should **only** add `--junitxml` for CI artifacts, and rely on the project config for coverage reporting.
- If no `addopts` or minimal flags, the generated workflow should include full coverage flags: `--cov=<src_dir> --cov-branch --cov-report=xml --cov-report=term-missing --junitxml=test-results.xml`

For Node.js/TypeScript version, check in order:

- `.nvmrc` file present → use `node-version-file: .nvmrc`
- `mise.toml` `[tools] node = "X"` → use `node-version: "X"`
- `package.json` `engines.node` field → use that version
- Neither found → default to `node-version: "22"` (current LTS)

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
If neither is found, look for a top-level Python package directory (a directory containing `__init__.py`).
If still not found, set source directory to `.` and add a note in Phase 1 summary asking the user to confirm.

For TypeScript: look for `src/` directory or check `tsconfig.json` `rootDir`.
If not found, default to `.` and ask the user to confirm in Phase 1 summary.

### 1-4. Check existing CI

Use Glob to check if `.github/workflows/` exists and list any existing workflow files.

### 1-5. Report detection summary

Present the detection summary to the user in this format:

```text
Detected project configuration:
  Language(s):       Python + Terraform  (or whatever was found)
  Package manager:   uv
  Python version:    3.12  (from mise.toml / requires-python / default)
  Test framework:    pytest
  Linter:            Ruff
  Source directory:  src/
  Terraform:         Yes (*.tf files found)
  Existing CI:       None (or list existing files)

Is this correct? If not, describe any corrections (e.g. "package manager is pip, not uv").
```

Wait for user confirmation before proceeding to Phase 2.

---

## Phase 2: Interactive CI Configuration

Ask the user a series of questions to configure the CI.

**Implementation note**: Use the AskUserQuestion tool for interactive questions. The tool supports
at most 4 questions per call, with at most 4 options per question.
Split into two calls if needed:

**Call 1** (CI steps + workflow structure):

- Question 1 — "Which CI steps would you like? (select all that apply)" `multiSelect: true`
  - "Lint + Test + Build + actionlint (essential; always recommended)"
  - "Secret scanning (gitleaks)"
  - "SAST (CodeQL + Trivy)"
  - "Dependency audit + PR title check"
- Question 2 — "Workflow file structure?" (2 options)
  - "Separate files: ci.yml + security.yml (recommended)"
  - "Single file: ci.yml"

**Call 2** (dependency management + visibility + security policy):

- Question 3 — "Dependency management automation?" (3 options)
  - "Renovate (recommended)"
  - "Dependabot (GitHub native)"
  - "Skip"
- Question 4 — "Repository visibility?" (2 options)
  - "Private / internal (default)"
  - "Public (enables fork PR support)"

Ask security policy and GHAS availability as a follow-up call when option 1 includes SAST (i.e., user selected "SAST"
or all options):

- "Security scan failure policy?" (3 options)
  - "Advisory — CRITICAL findings appear in Security tab, CI never fails (recommended)"
  - "Strict — Trivy exits with error on CRITICAL/HIGH/MEDIUM; CodeQL requires branch protection rule"
  - "Log-only — all findings visible in Security tab, CI never fails"
- "GitHub Advanced Security (GHAS) available?" (2 options)
  - "Yes — public repo or GHAS enabled: generate CodeQL job + SARIF upload (recommended)"
  - "No — private repo without GHAS: omit CodeQL job; set Trivy SARIF upload to continue-on-error"

For Terraform-only projects: always generate `terraform.yml` separately regardless of workflow
structure choice.

```text
Please answer the following to configure your CI:

1. Which CI steps do you want? (default: all)
   - [x] Lint + Test + Build + actionlint (essential; always recommended)
   - [x] Secret scanning (gitleaks)
   - [x] SAST (CodeQL + Trivy)
   - [x] Dependency audit + PR title check
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

5. Security scan failure policy: (asked only when SAST is selected)
   a) Advisory - findings appear in Security tab, CI never fails [recommended]
   b) Strict - Trivy fails CI directly; CodeQL requires branch protection rule
   c) Log-only - all findings visible in Security tab, CI never fails

6. GitHub Advanced Security (GHAS) available? (asked only when SAST is selected)
   a) Yes - public repo or GHAS enabled: generate CodeQL job + SARIF upload [default]
   b) No - private repo without GHAS: omit CodeQL job; Trivy SARIF upload set to continue-on-error
```

Wait for user responses before proceeding to Phase 3.

---

## Phase 3: File Generation

Based on Phase 1 detection and Phase 2 answers, generate the workflow files using the Write tool.

**Important security rules for ALL generated workflows:**

- Pin ALL third-party Actions to their git SHA hash, with a version comment
- Add `permissions: {}` at the workflow level to remove all default GITHUB_TOKEN permissions (equivalent to `permissions: none`);
  then explicitly grant the minimum required `permissions:` at the job level (e.g., `contents: read` for jobs that use `actions/checkout`)
- Always include `concurrency: cancel-in-progress: true` (use `${{ github.event_name == 'pull_request' }}` for `security.yml` that has a `schedule` trigger, to avoid cancelling scheduled CVE scans)
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

permissions: {}  # Restrict default GITHUB_TOKEN; each job sets its own minimum permissions

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
        uses: raven-actions/actionlint@205b530c5d9fa8f44ae9ed59f341a0db994aa6f8  # v2.1.2
```

---

### Template: ci.yml (Python + pip)

```yaml
# .github/workflows/ci.yml
# Actions versions are pinned to SHA for security.
# Dependabot/Renovate will keep them up to date automatically.

name: CI

on:
  pull_request:
  push:
    branches: [main]

permissions: {}  # Restrict default GITHUB_TOKEN; each job sets its own minimum permissions

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
      - uses: actions/setup-python@0b93645bdc8f3c7c6f8d3cf81c2a3a0e5e68a3a3  # v5.3.0
        with:
          python-version: "3.12"
          cache: pip
      - name: Install dependencies
        run: pip install -e .[dev]
      - name: Lint with Ruff
        run: python -m ruff check --output-format=github .
      - name: Format check with Ruff
        run: python -m ruff format --check .

  test:
    name: Test & Coverage
    runs-on: ubuntu-latest
    timeout-minutes: 15
    permissions:
      contents: read
      pull-requests: write  # Required for PR coverage comment
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - uses: actions/setup-python@0b93645bdc8f3c7c6f8d3cf81c2a3a0e5e68a3a3  # v5.3.0
        with:
          python-version: "3.12"
          cache: pip
      - name: Install dependencies
        run: pip install -e .[dev]
      # NOTE: --cov=src measures ALL files in src/, including untested ones (shown as 0%)
      # This gives an honest picture of total coverage. Adjust --cov=<your-src-dir> if needed.
      - name: Run tests with coverage
        run: |
          python -m pytest \
            --cov=src \
            --cov-branch \
            --cov-report=xml:coverage.xml \
            --cov-report=term-missing \
            --junitxml=test-results.xml
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
      - uses: actions/setup-python@0b93645bdc8f3c7c6f8d3cf81c2a3a0e5e68a3a3  # v5.3.0
        with:
          python-version: "3.12"
          cache: pip
      - name: Install build tool
        run: pip install build
      - name: Build package
        run: python -m build

  actionlint:
    name: Lint GitHub Actions workflows
    runs-on: ubuntu-latest
    timeout-minutes: 5
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - name: Run actionlint
        uses: raven-actions/actionlint@205b530c5d9fa8f44ae9ed59f341a0db994aa6f8  # v2.1.2
```

---

### Template: ci.yml (Python + poetry)

Generate the same structure as the uv variant, but replace setup/install/run steps in each job.
The common setup block for all poetry jobs:

```yaml
      - uses: actions/setup-python@0b93645bdc8f3c7c6f8d3cf81c2a3a0e5e68a3a3  # v5.3.0
        with:
          python-version: "3.12"
          cache: poetry  # Cache dependencies based on poetry.lock
      - name: Install Poetry
        # Pin to a specific version for reproducibility, e.g. "poetry==2.1.3"
        run: pip install "poetry>=2.0,<3.0"
      - name: Install dependencies
        run: poetry install --with dev
```

**Lint job** — after the common setup block, add:

```yaml
      - name: Lint with Ruff
        run: poetry run ruff check --output-format=github .
      - name: Format check with Ruff
        run: poetry run ruff format --check .
```

**Test job** — after the common setup block, replace the pytest step with:

```yaml
      - name: Run tests with coverage
        run: |
          poetry run pytest \
            --cov=src \
            --cov-branch \
            --cov-report=xml:coverage.xml \
            --cov-report=term-missing \
            --junitxml=test-results.xml
```

**Build job** — after the common setup block, replace the build step with:

```yaml
      - name: Build package
        run: poetry build
```

The `actionlint` job is identical to the uv variant.

---

### Template: ci.yml (TypeScript + npm + Biome)

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
  push:
    branches: [main]

permissions: {}  # Restrict default GITHUB_TOKEN; each job sets its own minimum permissions

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
        with:
          # "all" shows Changed Files + Unchanged Files sections (full project coverage visibility).
          # "changes" (default) shows only PR-modified files.
          file-coverage-mode: all
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
      - uses: raven-actions/actionlint@205b530c5d9fa8f44ae9ed59f341a0db994aa6f8  # v2.1.2
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

### Template: ci.yml (TypeScript + yarn or pnpm)

Same as the npm + Biome or npm + ESLint templates, but replace `actions/setup-node` cache and install steps:

**yarn:**

```yaml
      - uses: actions/setup-node@cdca7365b2dadb8aad0a33bc7601856ffabcc48e  # v4.3.0
        with:
          node-version-file: .nvmrc  # or: node-version: "22"
          cache: yarn
      - name: Install dependencies
        run: yarn install --frozen-lockfile
```

**pnpm:**

```yaml
      - uses: pnpm/action-setup@a7487c7e89a18df4991f7f222e4898a00d66ddde  # v4.1.0
        with:
          run_install: false
      - uses: actions/setup-node@cdca7365b2dadb8aad0a33bc7601856ffabcc48e  # v4.3.0
        with:
          node-version-file: .nvmrc  # or: node-version: "22"
          cache: pnpm
      - name: Install dependencies
        run: pnpm install --frozen-lockfile
```

Replace all `npm run` commands with `yarn` or `pnpm run` respectively.
Replace `npm ci` with `yarn install --frozen-lockfile` or `pnpm install --frozen-lockfile`.

> **Note:** `pnpm/action-setup` must be added **before** `actions/setup-node` for the `cache: pnpm` option to work.

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

permissions: {}  # Restrict default GITHUB_TOKEN; each job sets its own minimum permissions

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  # Do NOT cancel scheduled runs (they monitor for newly disclosed CVEs).
  # Only cancel duplicate PR builds.
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  secret-scan:
    name: Secret Scanning
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      contents: read
      pull-requests: read  # Required by gitleaks-action to list PR commits on pull_request events
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
        with:
          fetch-depth: 0  # full history for secret scanning
      - name: Run gitleaks
        uses: gitleaks/gitleaks-action@ff98106e4c7b2bc287b24eaf42907196329070c7  # v2.3.9
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # GITLEAKS_LICENSE: ${{ secrets.GITLEAKS_LICENSE }}  # required only for paid license

  dependency-audit:
    name: Dependency Audit
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      # NOTE: When generating this workflow, uncomment ONLY the block matching the detected
      # ecosystem below. Remove all other commented blocks. Do not leave placeholders in the
      # generated workflow.
      # --- Python (uv) ---
      # Requires: uv add pip-audit --dev
      # - uses: astral-sh/setup-uv@f0ec1fc3b38f5e7cd731bb6ce540c5af426746bb  # v5.4.0
      # - run: uv sync && uv run pip-audit
      # --- Python (pip) ---
      # - uses: actions/setup-python@0b93645bdc8f3c7c6f8d3cf81c2a3a0e5e68a3a3  # v5.3.0
      #   with: { python-version: "3.12", cache: pip }
      # - run: pip install -e .[dev] pip-audit && pip-audit
      # --- Python (poetry) ---
      # Requires: poetry add pip-audit --group dev
      # - uses: actions/setup-python@0b93645bdc8f3c7c6f8d3cf81c2a3a0e5e68a3a3  # v5.3.0
      #   with: { python-version: "3.12", cache: poetry }
      # - run: pip install "poetry>=2.0,<3.0" && poetry install --with dev && poetry run pip-audit
      # --- Node.js (npm) ---
      # - uses: actions/setup-node@cdca7365b2dadb8aad0a33bc7601856ffabcc48e  # v4.3.0
      #   with: { node-version-file: .nvmrc, cache: npm }
      # - run: npm ci && npm audit --audit-level=high
      # --- Node.js (yarn) ---
      # Note: yarn audit is yarn v1 only; yarn v2+ (berry) does not support this command
      # - uses: actions/setup-node@cdca7365b2dadb8aad0a33bc7601856ffabcc48e  # v4.3.0
      #   with: { node-version-file: .nvmrc, cache: yarn }
      # - run: yarn install --frozen-lockfile && yarn audit --level high
      # --- Node.js (pnpm) ---
      # - uses: pnpm/action-setup@a7487c7e89a18df4991f7f222e4898a00d66ddde  # v4.1.0
      # - uses: actions/setup-node@cdca7365b2dadb8aad0a33bc7601856ffabcc48e  # v4.3.0
      #   with: { node-version-file: .nvmrc, cache: pnpm }
      # - run: pnpm install --frozen-lockfile && pnpm audit --audit-level high
      # (Uncomment the block matching your language and package manager)

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
        uses: github/codeql-action/init@0d579ffd059c29b07949a3cce3983f0780820c98  # v4.32.6
        with:
          languages: ${{ matrix.language }}
          # `queries:` controls which rule suite runs:
          #   security-extended         = ADVISORY / LOG-ONLY  (default, broad security rules)
          #   security-and-quality      = STRICT               (adds quality rules, wider coverage)
          # NOTE: CodeQL never fails the action itself based on alert count.
          # Alerts always appear in the GitHub Security tab.
          # To block PR merges on CodeQL findings, enable "Code scanning" in branch protection rules
          # and configure the severity threshold in repository Settings > Code security.
          queries: security-extended
      - name: Autobuild
        uses: github/codeql-action/autobuild@0d579ffd059c29b07949a3cce3983f0780820c98  # v4.32.6
      - name: Analyze
        uses: github/codeql-action/analyze@0d579ffd059c29b07949a3cce3983f0780820c98  # v4.32.6
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
        uses: aquasecurity/trivy-action@57a97c7e7821a5776cebc9bb87c984fa69cba8f1  # 0.35.0
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
        uses: github/codeql-action/upload-sarif@0d579ffd059c29b07949a3cce3983f0780820c98  # v4.32.6
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
      - uses: amannn/action-semantic-pull-request@48f256284bd46cdaab1048c3721360e808335d50  # v6.1.1
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

permissions: {}  # Restrict default GITHUB_TOKEN; each job sets its own minimum permissions

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
      pull-requests: write  # Required for reviewdog inline PR comments
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2

      - uses: hashicorp/setup-terraform@5e8dbf3c6d9deaf4193ca7a8fb23f2ac83bb6c85  # v4.0.0

      - name: Terraform Format Check
        run: terraform fmt -check -recursive
        # If this fails: run `terraform fmt -recursive` locally and commit

      - name: Terraform Init
        run: terraform init -backend=false

      - name: Terraform Validate
        run: terraform validate

      - uses: actions/cache@cdf6c1fa76f9f475f3d7449005a359c84ca0f306  # v5.0.3
        with:
          path: ~/.tflint.d/plugins
          key: tflint-${{ runner.os }}-${{ hashFiles('.tflint.hcl') }}

      - uses: terraform-linters/setup-tflint@4cb9feea73331a35b422df102992a03a44a3bb33  # v6.2.1

      - name: Init tflint
        run: tflint --init

      - name: Run tflint (push — log only)
        if: github.event_name != 'pull_request'
        run: tflint --recursive --format compact

      - name: Run tflint (PR — inline comments via reviewdog)
        if: github.event_name == 'pull_request'
        uses: reviewdog/action-tflint@54a5e5aed57dcfbb4662ec548de876df33d6288d  # v1.25.0
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          reporter: github-pr-review  # posts tflint errors as inline review comments on PR diff
          flags: "--recursive"
          fail_on_error: "true"

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
        uses: aquasecurity/trivy-action@57a97c7e7821a5776cebc9bb87c984fa69cba8f1  # 0.35.0
        with:
          scan-type: config
          format: sarif
          output: trivy-iac.sarif
          severity: "CRITICAL,HIGH"
          exit-code: "0"
      - name: Upload results to Security tab
        uses: github/codeql-action/upload-sarif@0d579ffd059c29b07949a3cce3983f0780820c98  # v4.32.6
        if: always()
        with:
          sarif_file: trivy-iac.sarif

  actionlint:
    name: Lint GitHub Actions workflows
    runs-on: ubuntu-latest
    timeout-minutes: 5
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - name: Run actionlint
        uses: raven-actions/actionlint@205b530c5d9fa8f44ae9ed59f341a0db994aa6f8  # v2.1.2
```

---

### Template: renovate.json

> **Note on `group:allNonMajor`**: This preset bundles all non-major updates into a single weekly PR,
> which reduces PR noise but makes it harder to isolate regressions caused by individual dependency
> updates. If the user prefers fine-grained PRs (one per package), remove `"group:allNonMajor"` from
> `extends`. Ask the user during Phase 2 if they have a preference, or default to grouped (recommended
> for most projects).

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

> **SHA の鮮度確認 (任意)**
> テンプレートの SHA は時間とともに陳腐化します。Renovate/Dependabot 未導入の場合や
> 重要なアップデートが疑われる場合は、生成前に以下で最新 SHA を確認してください:
>
> ```sh
> # 1. 最新リリースタグを取得
> gh api repos/{owner}/{repo}/releases/latest --jq '.tag_name'
>
> # 2. タグの SHA を取得（通常タグ）
> gh api repos/{owner}/{repo}/git/ref/tags/{tag} --jq '.object.sha'
>
> # 3. annotated tag の場合はさらに dereference
> gh api repos/{owner}/{repo}/git/tags/{sha} --jq '.object.sha'
> ```
>
> Renovate/Dependabot を導入済みであれば自動更新されるため、この手順は省略可能です。

### Step 1: Determine files to generate

Based on Phase 2 choices, decide which files to create:

| Condition | Files to generate |
| --- | --- |
| Python + uv detected | `ci.yml` (Python + uv variant) |
| Python + poetry detected | `ci.yml` (Python + poetry variant) |
| Python + pip (fallback) | `ci.yml` (Python + pip variant) |
| TypeScript + npm + Biome | `ci.yml` (TypeScript + npm + Biome variant) |
| TypeScript + npm + ESLint | `ci.yml` (TypeScript + npm + ESLint variant) |
| TypeScript + yarn + Biome | `ci.yml` (TypeScript + npm + Biome variant, substituting yarn steps per yarn template block) |
| TypeScript + yarn + ESLint | `ci.yml` (TypeScript + npm + ESLint variant, substituting yarn steps per yarn template block) |
| TypeScript + pnpm + Biome | `ci.yml` (TypeScript + npm + Biome variant, substituting pnpm steps per pnpm template block) |
| TypeScript + pnpm + ESLint | `ci.yml` (TypeScript + npm + ESLint variant, substituting pnpm steps per pnpm template block) |
| Node.js (no TypeScript) | Same as TypeScript variant; set CodeQL language to `javascript`; omit `tsc` build steps and any `tsconfig.json` references |
| Terraform detected | `terraform.yml` |
| Security steps selected | `security.yml` |
| Renovate selected | `renovate.json` |
| Dependabot selected | `.github/dependabot.yml` |

**Combined projects (Python + Terraform):**
If both Python and Terraform are detected, generate both `ci.yml` (Python variant) and `terraform.yml` as separate files.
Do NOT merge them into a single file — keeping them separate allows independent triggering via `paths` filters.

**Combined projects (Python + TypeScript):**
If both Python and TypeScript are detected in the same repository, generate a single `ci.yml` that contains separate jobs for each language:
- Python jobs: `lint-python`, `test-python`, `build-python`
- TypeScript jobs: `lint-ts`, `test-ts`, `build-ts`
- One shared `actionlint` job at the end
Use the respective language templates for each job group's steps.

### Step 2: Customize templates

Before writing files, substitute these values from Phase 1 detection:

- Package manager commands (`uv run`, `pip`, `npm ci`, `yarn`, `pnpm install`)
- For **yarn**: replace `cache: npm` → `cache: yarn`; `npm ci` → `yarn install --frozen-lockfile`; `npm run` → `yarn`
- For **pnpm**: add `pnpm/action-setup` before `actions/setup-node`; replace `cache: npm` → `cache: pnpm`; `npm ci` → `pnpm install --frozen-lockfile`; `npm run` → `pnpm run`
- Source directory in `--cov=<src_dir>` and `coverage.include`
- **Python pytest command**: If `pyproject.toml` `[tool.pytest.ini_options].addopts` already contains coverage flags,
  simplify the workflow pytest command to only: `pytest --junitxml=test-results.xml` (rely on project config for coverage).
  Otherwise, use the full template with `--cov=<src_dir> --cov-branch --cov-report=xml --cov-report=term-missing --junitxml=test-results.xml`
- Python version from `mise.toml` or `pyproject.toml` requires-python
- Node.js version: if `.nvmrc` exists → `node-version-file: .nvmrc`; otherwise → `node-version: "<detected-version>"` (fallback: `"22"`)
  Remove the `node-version-file` key from templates if `.nvmrc` is absent
- CodeQL language (`python`, `javascript`, `typescript`)
- If repository is **Public**, add this to fork PR-sensitive jobs (coverage comment):

  ```yaml
  # Restrict on fork PRs (no write permissions available from forks)
  if: github.event.pull_request.head.repo.full_name == github.repository
  ```

- **GHAS availability from Phase 2** (applies when SAST was selected):
  - **GHAS = Yes**: Generate the full `sast` job (CodeQL) and Trivy `upload-sarif` without `continue-on-error`
  - **GHAS = No**: **Omit the `sast` job entirely**; add `continue-on-error: true` to Trivy `upload-sarif` steps
    with a comment explaining the requirement:

    ```yaml
          - name: Upload Trivy results to Security tab
            uses: github/codeql-action/upload-sarif@0d579ffd059c29b07949a3cce3983f0780820c98  # v4.32.6
            if: always()
            with:
              sarif_file: trivy-results.sarif
            # SARIF upload requires GitHub Advanced Security for private repos.
            # Enable GHAS and remove continue-on-error to surface findings in the Security tab.
            continue-on-error: true
    ```

### Step 3: Apply security failure policy from Phase 2

**Advisory (default):**

- CodeQL: `queries: security-extended` — alerts appear in Security tab, CI never fails on findings
- Trivy: `exit-code: "0"`, `severity: "CRITICAL,HIGH"`

**Strict:**

- CodeQL: `queries: security-and-quality` — broader rule coverage; alerts still only appear in Security tab.
  To actually block PR merges, configure branch protection rules to require the "CodeQL" status check
  and set the alert severity threshold in repository Settings → Code security → Code scanning.
- Trivy: `exit-code: "1"`, `severity: "CRITICAL,HIGH,MEDIUM"` — Trivy **does** fail the action directly

**Log-only:**

- CodeQL: `queries: security-extended`, no change — findings visible in Security tab only
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

💡 Optional optimizations (not applied by default):
   - Add `paths:` filters to ci.yml to skip runs on doc-only changes:
       on:
         pull_request:
           paths: ['src/**', 'tests/**', 'pyproject.toml', 'package.json']
         push:
           branches: [main]
           paths: ['src/**', 'tests/**', 'pyproject.toml', 'package.json']
   - terraform.yml already uses paths filters for *.tf files (no change needed)
   - Remove "group:allNonMajor" from renovate.json for per-package PRs
```

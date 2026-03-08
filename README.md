# ai-skills-collection

[![Markdown lint](https://github.com/yasuwrldhyper/ai-skills-collection/actions/workflows/ci.yml/badge.svg)](https://github.com/yasuwrldhyper/ai-skills-collection/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Node.js 22+](https://img.shields.io/badge/node-22+-brightgreen.svg)](https://nodejs.org/)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-skills-blueviolet)](https://claude.ai/code)

A curated collection of [Claude Code](https://claude.ai/code) skills focused on backend development workflows. Drop these skills into any project to supercharge your AI-assisted development.

## Skills

### Custom Skills (`skills/` directory)

| Skill | Command | Description |
| --- | --- | --- |
| [code-review](./skills/code-review/) | `/code-review <path>` | 5 specialist agents review your code in parallel and generate a unified report |
| [gcp-expert](./skills/gcp-expert/) | `/gcp-expert [question]` | GCP service selection, implementation patterns, and security best practices |
| [generate-ci](./skills/generate-ci/) | `/generate-ci [path]` | Auto-detects your language and interactively generates GitHub Actions CI workflows |
| [worktree-implement](./skills/worktree-implement/) | `/worktree-implement <task>` | Creates an isolated `git worktree` environment for each task automatically |
| [resolve-pr-reviews](./skills/resolve-pr-reviews/) | `/resolve-pr-reviews [PR#]` | Fetches unresolved PR review comments and automates fixes, replies, and push |
| [review-comment-convention](./skills/review-comment-convention/) | `/review-comment-convention` | Interactively configures PR review comment priority conventions |

### Sample Projects

| Directory | Contents |
| --- | --- |
| [generate-ci/](./generate-ci/) | Demo projects for `/generate-ci` (Python / TypeScript / Terraform) |
| [agentteam-review/](./agentteam-review/) | Intentionally flawed code samples for `/code-review` demos |

## Quick Start

### Add skills to your project

One-liner to install 3 skills + review convention (default: P1–P5, English):

```sh
bash <(curl -fsSL https://raw.githubusercontent.com/yasuwrldhyper/ai-skills-collection/main/scripts/setup-project.sh) p1-en
```

Available presets:

```sh
# P1–P5 priority system
bash <(curl -fsSL https://raw.githubusercontent.com/yasuwrldhyper/ai-skills-collection/main/scripts/setup-project.sh) p1-en   # English
bash <(curl -fsSL https://raw.githubusercontent.com/yasuwrldhyper/ai-skills-collection/main/scripts/setup-project.sh) p1-ja   # Japanese

# must/imo/nits/fyi priority system
bash <(curl -fsSL https://raw.githubusercontent.com/yasuwrldhyper/ai-skills-collection/main/scripts/setup-project.sh) must-en  # English
bash <(curl -fsSL https://raw.githubusercontent.com/yasuwrldhyper/ai-skills-collection/main/scripts/setup-project.sh) must-ja  # Japanese
```

Skills installed:

- `/worktree-implement` — isolated worktree environments per task
- `/resolve-pr-reviews` — automated PR review resolution
- `/review-comment-convention` — review priority convention setup

### Install individual skills via npx

```sh
npx skills add yasuwrldhyper/ai-skills-collection@worktree-implement -y
npx skills add yasuwrldhyper/ai-skills-collection@resolve-pr-reviews -y
npx skills add yasuwrldhyper/ai-skills-collection@review-comment-convention -y
npx skills add yasuwrldhyper/ai-skills-collection@generate-ci -y
npx skills add yasuwrldhyper/ai-skills-collection@code-review -y
npx skills add yasuwrldhyper/ai-skills-collection@gcp-expert -y
```

### Clone and explore this repository

```sh
# Install required tools (requires mise)
mise install

# Install community skills
mise run setup:skills
```

## Prerequisites

| Tool | Purpose | Install |
| --- | --- | --- |
| [Claude Code](https://claude.ai/code) | Skill runtime | See official docs |
| [mise](https://mise.jdx.dev/) | Tool version management | `curl https://mise.run \| sh` |
| Node.js 22+ | `npx skills` command | Auto-installed via `mise install` |

For AgentTeam features (`/code-review`):

- Set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in your environment
- Install tmux (required when `teammateMode: "tmux"` is configured)

## Review Convention Presets

The `templates/review-convention/` directory includes 4 ready-to-use presets:

| Preset | Priority system | Language |
| --- | --- | --- |
| `p1-en` | P1 (Critical) – P5 (Optional) | English |
| `p1-ja` | P1 (緊急) – P5 (改善提案) | Japanese |
| `must-en` | must / imo / nits / fyi | English |
| `must-ja` | must / imo / nits / fyi | Japanese |

To customize interactively with Claude Code:

```sh
/review-comment-convention setup
```

## Repository Structure

```text
.
├── skills/                        # Skill definitions (SKILL.md)
│   ├── code-review/
│   ├── gcp-expert/
│   ├── generate-ci/
│   ├── resolve-pr-reviews/
│   ├── review-comment-convention/
│   └── worktree-implement/
├── generate-ci/                   # Sample projects for generate-ci skill
│   └── sample/
│       ├── python/
│       ├── typescript/
│       └── terraform/
├── agentteam-review/              # Sample code for code-review skill
│   └── src/sample_app/
├── templates/review-convention/   # Review convention presets
├── scripts/
│   └── setup-project.sh          # One-liner setup script
├── .claude/skills/                # Claude Code skill entry points (symlinks)
├── mise.toml                      # Tool versions and task definitions
├── skills-lock.json               # Community skills hash lock
└── CLAUDE.md                      # Claude Code project instructions
```

## Contributing

Contributions are welcome — new skills, improvements to existing ones, or additional sample projects. See [CONTRIBUTING.md](./.github/CONTRIBUTING.md).

## License

[MIT](./LICENSE)

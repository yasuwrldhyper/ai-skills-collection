# Contributing Guide

Feedback, bug reports, new skill proposals, and pull requests are all welcome.

## Setup

```sh
# Clone the repository
git clone https://github.com/yasuwrldhyper/ai-skills-collection.git
cd ai-skills-collection

# Install required tools
mise install

# Install community skills
mise run setup:skills

# Install git pre-commit hooks
mise run setup:hooks
```

## Ways to Contribute

### Bug Reports & Improvement Suggestions

Use the Issue templates to report bugs or propose improvements.

### Adding a New Skill

1. Create `skills/<skill-name>/SKILL.md`
2. Write `SKILL.md` as an instruction file for Claude Code (refer to [existing skills](../skills/) for examples)
3. Create a symlink from `.claude/skills/<skill-name>` to `../../skills/<skill-name>`
4. Add an entry to the skills table in `CLAUDE.md`

You can use the `/skill-creator` command to help generate the skill:

```sh
# Run inside Claude Code
/skill-creator
```

### Improving an Existing Skill

- Edit `skills/<skill-name>/SKILL.md` directly
- Describe the changes in your PR

### Adding a Sample Project

- Create a `<skill-name>/` directory
- Add a `README.md` explaining the purpose, usage, and prerequisites

## Pull Request Process

1. Create a branch (`feat/xxx` or `fix/xxx` naming is recommended)
2. Make your changes
3. Verify documentation passes lint (the pre-commit hook runs this automatically)

   ```sh
   mise run lint
   ```

4. Open a PR following the PR template

## Lint Scope

`mise run lint` checks all Markdown files we maintain:

| Included | Excluded |
| --- | --- |
| `README.md`, `CLAUDE.md`, `*/README.md` | `skills/**` (SKILL.md instruction files) |
| `.github/**/*.md` | `templates/**` (pre-formatted convention templates) |
| | `.claude/**`, `.agent/**`, `.agents/**` (symlinks / community content) |

## Code Style

- Write `SKILL.md` files as clear instruction prompts that Claude Code can interpret
- Keep sample code minimal — prefer working examples over over-engineered abstractions
- Write documentation in English (technical terms and code identifiers stay as-is)
- Provide `.env.example` for environment variables; add `.env` to `.gitignore`

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](../LICENSE).

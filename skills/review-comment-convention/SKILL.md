---
name: review-comment-convention
description: PRレビューコメントの優先度規約（P1–P5 または must/imo/nits/fyi）を対話的に設定し、copilot-instructions.md と CLAUDE.md に書き込む。出力言語（日本語・英語・バイリンガル）も設定可能。
argument-hint: "[setup | show | apply <file> | preset <name>]"
allowed-tools: Read, Write, Edit, Glob, Bash, AskUserQuestion
---

# /review-comment-convention Skill

Set up code review comment conventions for your project. Conventions are written to
`.github/copilot-instructions.md` (GitHub Copilot) and/or `CLAUDE.md` (Claude Code),
so that AI reviewers and human reviewers share the same priority labeling system.

---

## Argument Routing

Parse `$ARGUMENTS` and branch:

| Argument | Action |
|----------|--------|
| _(empty)_ or `setup` | Run Phase 1 → 2 → 3 → 4 (full interactive flow) |
| `show` | Run Phase 1 (detect only), then print current convention and exit |
| `apply <file>` | Run Phase 1 (detect only), skip Phase 2–3, use existing convention block, write to `<file>` |
| `preset <name> [files...]` | Non-interactive mode. Skip Phase 1–2, generate from preset, write to targets. See **Preset Mode** below |

---

## Preset Mode

When `$ARGUMENTS` starts with `preset`, skip all interactive phases and apply a convention directly.

### Syntax

```
/review-comment-convention preset <preset-name> [file1 file2 ...]
```

If no target files are specified, write to **both** `.github/copilot-instructions.md` and `CLAUDE.md`.

### Available Presets

| Preset | Style | Language |
|--------|-------|----------|
| `p1-ja` | P1–P5 | Japanese |
| `p1-en` | P1–P5 | English |
| `must-ja` | must / imo / nits / fyi | Japanese |
| `must-en` | must / imo / nits / fyi | English |

### Behavior

1. Parse preset name → map to style + language
2. Generate the convention block (same output as Phase 3, using the mapped style and language)
3. Write to target files (same logic as Phase 4)
4. Display completion message

If the preset name is unrecognized, print available presets and exit.

---

## Phase 1: Detect Existing Convention

Search for existing convention definitions.

### 1-1. Check target files

Use Glob and Read to look for:

- `.github/copilot-instructions.md`
- `CLAUDE.md`
- Any file matching `.github/CONTRIBUTING.md` or `docs/reviewing.md`

### 1-2. Extract existing convention block

In each found file, search for a section heading matching any of:
- `## Code Review Comment Convention`
- `## コードレビューコメント規約`
- `## Review Labels`
- `## レビュー規約`

If found, read its content and store as `EXISTING_CONVENTION`.

### 1-3. Report

- If `EXISTING_CONVENTION` is found: show file path and a brief preview (first 5 lines), then ask if the user wants to overwrite or cancel.
  - If `show` argument: print the full block and exit.
- If nothing found and `show` argument: print "No convention defined yet. Run `/review-comment-convention setup` to create one." and exit.
- If `apply <file>` and `EXISTING_CONVENTION` is found: write it to `<file>` and exit (skip Phases 2–3).

---

## Phase 2: Interactive Configuration

Use AskUserQuestion for the following two calls.

### Call 1 — Style and Language

**Question 1** — "Which priority label style would you like to use?" (header: "Label style")

Options:
- `P1–P5` — numeric scale; P1 = must fix, P5 = informational only
- `must / imo / nits / fyi` — Google-style semantic labels
- `Both` — P1–P5 as primary labels, with semantic aliases shown in parentheses

**Question 2** — "Which language should review comments be written in?" (header: "Language")

Options:
- `Japanese` — comments in Japanese (日本語)
- `English` — comments in English
- `Bilingual` — Japanese primary with English translation in parentheses

### Call 2 — Target Files

**Question 3** — "Which files should the convention be written to?" (header: "Target files", multiSelect: true)

Options:
- `.github/copilot-instructions.md` — applied to GitHub Copilot code review
- `CLAUDE.md` — applied to Claude Code sessions
- Both (select both above)

---

## Phase 3: Generate Convention Block

Based on Phase 2 selections, generate a Markdown section.

### P1–P5 style, Japanese

```markdown
## コードレビューコメント規約

レビューコメントは**日本語**で記述すること。
レビューコメントには以下の優先度プレフィックスを付与する。
レビュイーはレベルに応じて対応を判断すること。

| レベル | 意味 | 対応 |
|--------|------|------|
| **P1** | 必須修正（バグ・セキュリティ・仕様違反） | マージ前に修正必須 |
| **P2** | 強く推奨（パフォーマンス・保守性に明確な影響あり） | 原則修正。議論の余地あり |
| **P3** | 提案（設計改善・可読性向上） | 対応は任意。次回以降でも可 |
| **P4** | 軽微な指摘（typo・スタイル・命名の好み） | nits。完全任意 |
| **P5** | 情報共有・参考リンク（修正不要） | fyi。アクション不要 |

### 書き方の例

```
P1: 認証トークンがログに出力されています。即時修正が必要です。
P2: この N+1 クエリはページングが増えると深刻になります。
P3: Strategy パターンで整理できそうです（急ぎではありません）。
P4: 変数名 `data` より `userList` の方が意図が伝わりやすいです。
P5: 参考: https://example.com/best-practices
```
```

### P1–P5 style, English

```markdown
## Code Review Comment Convention

Prefix each review comment with a priority label.
Reviewees should decide their response based on the level.

| Level | Meaning | Action |
|-------|---------|--------|
| **P1** | Must fix (bug, security, spec violation) | Fix before merge |
| **P2** | Strongly recommended (performance, maintainability impact) | Fix unless strong reason not to |
| **P3** | Suggestion (design improvement, readability) | Optional; can defer |
| **P4** | Minor (typo, style, naming preference) | Nits; completely optional |
| **P5** | Informational / reference link (no change needed) | FYI; no action required |

### Examples

```
P1: Auth token is written to logs. Must fix before merge.
P2: This N+1 query will degrade as pagination grows.
P3: This could be refactored with a Strategy pattern (no rush).
P4: `data` → `userList` would better convey intent.
P5: Reference: https://example.com/best-practices
```
```

### P1–P5 style, Bilingual

Same as Japanese, but add English translations in parentheses in each cell:

```markdown
| **P1** | 必須修正（バグ・セキュリティ・仕様違反）*(must fix)* | マージ前に修正必須 *(required before merge)* |
```

And include a bilingual examples section.

### must / imo / nits / fyi style, Japanese

```markdown
## コードレビューコメント規約

レビューコメントは**日本語**で記述すること。
レビューコメントには以下のラベルを先頭に付与する。

| ラベル | 意味 | 対応 |
|--------|------|------|
| **must** | 必須修正（バグ・セキュリティ・仕様違反） | マージ前に修正必須 |
| **should** | 強く推奨（品質・保守性に影響） | 原則修正 |
| **imo** | 個人的な提案・好み（設計・命名） | 任意。議論歓迎 |
| **nits** | 軽微な指摘（typo・フォーマット） | 完全任意 |
| **fyi** | 情報共有（修正不要） | アクション不要 |

### 書き方の例

```
must: 認証トークンがログに出力されています。
should: この N+1 クエリはページングが増えると影響が大きくなります。
imo: Strategy パターンの方がスッキリするかもしれません。
nits: 末尾のカンマが抜けています。
fyi: 参考: https://example.com/best-practices
```
```

### must / imo / nits / fyi style, English

```markdown
## Code Review Comment Convention

Prefix each review comment with one of the following labels.

| Label | Meaning | Action |
|-------|---------|--------|
| **must** | Blocking issue (bug, security, spec violation) | Fix before merge |
| **should** | Strongly recommended (quality, maintainability) | Fix unless strong reason |
| **imo** | Subjective suggestion (design, naming preference) | Optional; open to discussion |
| **nits** | Minor style / typo / formatting | Completely optional |
| **fyi** | Informational only, no change needed | No action required |

### Examples

```
must: Auth token is written to logs. Fix before merge.
should: N+1 query will degrade with larger page sizes.
imo: A Strategy pattern might clean this up nicely.
nits: Missing trailing comma.
fyi: Reference: https://example.com/best-practices
```
```

### Both style (P1–P5 primary, semantic aliases in parentheses)

Combine both tables: show P1–P5 as the label column, add a "Alias" column:

```markdown
| Level | Alias | Meaning | Action |
|-------|-------|---------|--------|
| **P1** | must | ... | ... |
| **P2** | should | ... | ... |
| **P3** | imo | ... | ... |
| **P4** | nits | ... | ... |
| **P5** | fyi | ... | ... |
```

---

## Phase 4: Apply to Target Files

Write the generated convention block to each selected target file.

### Writing to `.github/copilot-instructions.md`

1. Use Glob to check if the file exists.
2. **File does not exist** → Create it with the following structure:

```markdown
# Copilot Instructions

<!-- Project-specific instructions for GitHub Copilot code review -->

<generated convention block>
```

3. **File exists** → Use Read to check for an existing convention section.
   - Section found → Replace it with the new block using Edit.
   - Section not found → Append the new block at the end of the file.

### Writing to `CLAUDE.md`

1. Read the file.
2. Search for an existing convention section (`## コードレビューコメント規約` or `## Code Review Comment Convention` or `## Review Labels` or `## レビュー規約`).
   - Section found → Replace it with the new block using Edit.
   - Section not found → Append the new block at the end of the file.

### Completion message

```
✅ Review comment convention applied

   Style:    P1–P5  (or: must/imo/nits/fyi, or: Both)
   Language: 日本語  (or: English, or: Bilingual)

   Written to:
   ✓  .github/copilot-instructions.md
   ✓  CLAUDE.md

To update: /review-comment-convention setup
To view:   /review-comment-convention show
```

---

## Error Handling

| Situation | Action |
|-----------|--------|
| `apply <file>` but no existing convention found anywhere | Ask user if they want to run the full `setup` flow first |
| Target file is in a read-only location | Report error, skip that file, continue with others |
| User selects no target files | Ask again; do not proceed with empty selection |
| File write fails | Show error message with the file path |

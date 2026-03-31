---
name: branch-strategy
description: >-
  ブランチ戦略の提案・設定・規約チェックを行う。プロジェクト特性（チーム規模・リポジトリ構成・
  デプロイフロー・リリースサイクル）をヒアリングし、5つの基本戦略とデプロイフローオプションの
  中から最適解をスペシャリストとして提案する。設定は .branch-strategy.json に保存し、
  Claude Code フックでブランチ名の自動チェックも可能。ブランチ戦略の設定・見直し・命名規約の
  統一を行いたい時、新しいリポジトリをセットアップする時、チームでブランチ運用を統一したい時に
  積極的に使うこと。
argument-hint: "[suggest | setup | check | show]"
allowed-tools: Read, Write, Edit, Glob, Bash, AskUserQuestion
---

# /branch-strategy Skill

`$ARGUMENTS` に応じてフローを切り替える:

| 引数 | 動作 |
|------|------|
| (空) / `suggest` | Phase 1 → Phase 2（提案のみ） |
| `setup` | Phase 1 → Phase 2 → Phase 3 → Phase 4 |
| `check` | Phase 5（既存ブランチの規約チェック） |
| `show` | `.branch-strategy.json` の内容を表示して終了 |

---

## ブランチ戦略の知識体系

このスキルを実行する際、以下の知識を専門家として活用する。決定マトリクスで機械的に選ぶのではなく、プロジェクトの状況を理解した上で「なぜこの戦略が適切か」を文脈と共に提案すること。

### 5つの基本戦略

**GitHub Flow**
- ブランチ: `main` + 短命 feature ブランチのみ
- `main` は常にデプロイ可能。feature → PR → `main` のシンプルなフロー
- 適合: 小〜中規模チーム、継続的デプロイ、SaaS プロダクト
- 注意: リリース管理が不要な場合向け。複数バージョン並行は不得意

**Git Flow**
- ブランチ: `main`, `develop`, `feature/*`, `release/*`, `hotfix/*`
- 厳格なマージ規律が必要。`develop` がインテグレーションポイント
- 適合: バージョン管理が必要なソフトウェア、複数バージョン並行メンテ
- 注意: 大規模チームでは `develop` がボトルネックになりマージ競合が頻発

**Trunk-based Development**
- ブランチ: `main` + 非常に短命なブランチ（1〜2日で main にマージ）
- feature flag で未完成機能を隠す。高頻度のインテグレーションが前提
- 適合: 高成熟CI/CD 環境、少人数精鋭チーム、高速イテレーション
- 注意: CI/CD が未成熟だと壊れた main が頻発する。feature flag 管理コストも発生

**GitLab Flow（環境ブランチ方式）**
- ブランチ: `main` + `staging`, `production` 等の環境ブランチ
- feature → `main` → `staging` → `production` と環境間をマージ昇格
- 適合: 複数のデプロイ環境がある場合、リリース承認フローが必要な場合
- **重大な制約**: 全 feature が同時昇格するため、施策ごとにローンチ時期が異なるモノレポとは相性が最悪

**Release-branch**
- ブランチ: `main` + `release/vX.Y` の長命リリースブランチ
- 新バージョンは `main` から切り出し、bug fix は cherry-pick で適用
- 適合: バージョンリリース形式だが `develop` ほど複雑なフローが不要な場合

### デプロイフローオプション

基本戦略に重ねて選択する（選択しない場合は `null`）:

**環境ブランチ方式** (`"environment-branches"`)
```
main(prod)
  ↑ merge
staging
  ↑ merge
qa
  ↑ merge
develop
  ↑ merge
feat/xxx
```
「承認者が環境間のマージを実施」という運用に向く。**ただしモノレポで施策ローンチ時期が独立している場合は禁止**（全施策が一括で昇格してしまう）。

**タグ + デプロイトリガー方式** (`"tag-deploy"`)
```
main(常にデプロイ可能)
  ↑ merge
feat/xxx

tag: v1.0.0-rc.1 → QA 環境にデプロイ
tag: v1.0.0-rc.2 → Staging 環境にデプロイ
tag: v1.0.0      → 本番デプロイ
```
ブランチはシンプルに保ちつつ、タグで環境を制御。モノレポにも対応しやすい。

### アンチパターン（避けるべき組み合わせ）

| 条件 | アンチパターン | 問題 | 推奨代替 |
|------|--------------|------|---------|
| モノレポ + 施策ごとに独立したローンチ | 環境ブランチ方式 | 全施策が同時昇格。「施策AだけQAに出す」が不可能。リリーストレイン問題 | trunk-based + feature flag、またはタグ方式 |
| モノレポ + 大規模チーム（15人以上） | Git Flow | `develop` が競合のボトルネック。マージ地獄 | trunk-based |
| ポリレポ + マイクロサービス | Git Flow | サービスごとに独立リリースなのにフローが重すぎる | GitHub Flow or trunk-based |
| ソロ / 小規模チーム（〜5人） | Git Flow | オーバーヘッドがメリットを上回る | GitHub Flow |
| CI/CD が手動またはテストが薄い | trunk-based | 壊れたコードが `main` に入りやすい | GitHub Flow（PRで保護） |
| 複数バージョンを同時メンテ | GitHub Flow / trunk-based | リリースブランチの管理が不可能 | Git Flow or release-branch |

---

## Phase 1: ヒアリング

**目的**: プロジェクトの本質的な特性を把握し、適切な戦略提案に必要な情報を得る。一度に全部聞かず、段階的に深掘りすること。

### 1-1. 初回ヒアリング

AskUserQuestion で以下を1度に質問:
- プロダクトの種類（Web API / フロントエンド含む Web アプリ / ライブラリ / モバイルバックエンド / その他）
- リポジトリ構成（モノレポ / ポリレポ / 単一サービス）
- チーム規模（ソロ / 2-5人 / 6-15人 / 15人以上）

### 1-2. 深掘りヒアリング

1-1 の回答を踏まえて、必要な質問のみ追加で聞く。全部聞く必要はない。

以下の観点で情報が不足していれば質問する:
- **モノレポの場合**: 施策・機能のローンチ時期は同期（全機能同時リリース）か独立（機能ごとに別タイミング）か？
- **デプロイ環境**: QA / ステージング / 本番 など何段階あるか？環境ごとに承認フローがあるか？
- **リリース頻度**: 随時デプロイ / 週次・月次定期リリース / バージョン番号管理（semver等）
- **CI/CD 成熟度**: 手動デプロイ / 基本的なCIはある / フルCI/CDで自動デプロイ
- **ホットフィックス**: 本番の緊急修正が必要になる頻度？（高い場合は `hotfix/` ブランチが必要）
- **バージョン並行**: v1.x と v2.x を同時にメンテするような状況があるか？

---

## Phase 2: 戦略提案

**目的**: ヒアリング結果を元に、スペシャリストとして最適な構成を1つ提案する。

### 提案に含める内容

1. **推奨構成** - 基本戦略 + デプロイフローオプション（必要な場合）の組み合わせ
2. **選定理由** - なぜこのプロジェクトにこの構成が適合するのか、具体的に説明
3. **避けた選択肢** - 検討したが選ばなかった戦略と、その理由（特にアンチパターンに該当する場合は明示的に説明）
4. **ブランチトポロジー** - ASCII図で可視化
5. **命名規約テーブル** - ブランチプレフィックスと用途
6. **トレードオフと注意点**

### 確認

提案後、ユーザーに確認:
```
この戦略で進めますか？
- はい → setup の場合は Phase 3 へ、suggest の場合は終了
- カスタマイズしたい → 変更点を聞いて反映
- 別の選択肢を見たい → 他の戦略を提示
```

---

## Phase 3: 設定書き出し（`setup` 時のみ）

### 3-1. `.branch-strategy.json` を生成

下記スキーマを元に、選択した戦略の設定を生成してプロジェクトルートに書き出す:

```json
{
  "strategy": "<github-flow|git-flow|trunk-based|gitlab-flow|release-branch>",
  "deployFlow": "<null|environment-branches|tag-deploy>",
  "repoType": "<single|monorepo|polyrepo>",
  "mainBranch": "main",
  "developBranch": "<null|develop>",
  "environmentBranches": [],
  "branchPrefixes": {
    "feature": "feat/",
    "bugfix": "fix/",
    "hotfix": "hotfix/",
    "release": "release/",
    "docs": "docs/",
    "refactor": "refactor/",
    "test": "test/",
    "chore": "chore/"
  },
  "branchPattern": "^(feat|fix|hotfix|release|docs|refactor|test|chore)/[a-z0-9][a-z0-9-]{2,40}$",
  "protectedBranches": ["main"],
  "maxBranchNameLength": 60,
  "requireIssueNumber": false,
  "issuePattern": null
}
```

戦略ごとの設定差分:
- **Git Flow**: `developBranch: "develop"`, `protectedBranches: ["main", "develop"]`
- **環境ブランチ方式**: `environmentBranches` に実際の環境名を設定（例: `["develop", "qa", "staging"]`）、`protectedBranches` に追加
- **trunk-based**: `branchPattern` を短命ブランチ向けに調整（prefix 必須だが期間の短さを README 等で説明）

### 3-2. `CLAUDE.md` に Branch Strategy セクションを追記

`## Branch Strategy` セクションが存在する場合は置換し、ない場合は末尾に追記:

```markdown
## Branch Strategy

Strategy: <戦略名>
Deploy flow: <フロー名 or なし>
Repo type: <monorepo|polyrepo|single>

### Branch naming convention

| Prefix | Purpose |
|--------|---------|
| feat/ | New feature |
| fix/ | Bug fix |
| hotfix/ | Emergency production fix |
| release/ | Release preparation |
| docs/ | Documentation |
| refactor/ | Refactoring |
| test/ | Test additions |
| chore/ | Maintenance, dependency updates |

Protected branches: <list>
Pattern: `<branchPattern>`
```

---

## Phase 4: フック設定（`setup` 時のみ）

### 4-1. ユーザーに確認

「Claude Code のフックで、ブランチ作成時に命名規約を自動チェックしますか？（yes / no）」

AskUserQuestion を使う。No の場合はこの Phase をスキップ。

### 4-2. フックスクリプトを書き出す

`scripts/hooks/check-branch-convention.sh` を以下の内容で作成:

```bash
#!/usr/bin/env bash
# Claude Code PreToolUse hook: validate branch naming convention
# Reads tool call JSON from stdin; blocks if branch name violates .branch-strategy.json

set -euo pipefail

# Read the full hook payload
PAYLOAD=$(cat)

# Extract the bash command from the tool input
COMMAND=$(echo "$PAYLOAD" | jq -r '.tool_input.command // empty')

# Extract branch name from branch-creation commands
# git checkout -b <name>    git checkout -b <name> <base>
# git branch <name>         git branch <name> <base>
# git switch -c <name>      git switch -c <name>
BRANCH=""
if echo "$COMMAND" | grep -qE 'git (checkout|switch) -[cCb]'; then
  BRANCH=$(echo "$COMMAND" | sed -E 's/.*git (checkout|switch) -[cCb][[:space:]]+([^[:space:]]+).*/\2/')
elif echo "$COMMAND" | grep -qE 'git branch [^-]'; then
  BRANCH=$(echo "$COMMAND" | sed -E 's/.*git branch[[:space:]]+([^[:space:]]+).*/\1/')
fi

# Exit 0 (allow) if no branch creation detected
[ -z "$BRANCH" ] && exit 0

# Find project root by locating .branch-strategy.json
PROJECT_ROOT=""
DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
if [ -f "$DIR/.branch-strategy.json" ]; then
  PROJECT_ROOT="$DIR"
else
  # Walk up (max 5 levels)
  CHECK="$DIR"
  for _ in 1 2 3 4 5; do
    CHECK=$(dirname "$CHECK")
    if [ -f "$CHECK/.branch-strategy.json" ]; then
      PROJECT_ROOT="$CHECK"
      break
    fi
  done
fi

# Exit 0 (allow) if no config found
[ -z "$PROJECT_ROOT" ] && exit 0

CONFIG="$PROJECT_ROOT/.branch-strategy.json"
PATTERN=$(jq -r '.branchPattern // empty' "$CONFIG")
PROTECTED=$(jq -r '.protectedBranches[]?' "$CONFIG")
MAX_LEN=$(jq -r '.maxBranchNameLength // 60' "$CONFIG")

# Protected branches are always allowed
while IFS= read -r pb; do
  [ "$BRANCH" = "$pb" ] && exit 0
done <<< "$PROTECTED"

# Exit 0 if no pattern configured
[ -z "$PATTERN" ] && exit 0

# Validate length
if [ "${#BRANCH}" -gt "$MAX_LEN" ]; then
  echo "Branch name too long: '$BRANCH' (${#BRANCH} chars, max $MAX_LEN)" >&2
  echo "Tip: shorten the description part after the prefix" >&2
  exit 2
fi

# Validate pattern
if ! echo "$BRANCH" | grep -qE "$PATTERN"; then
  PREFIXES=$(jq -r '.branchPrefixes | to_entries[] | "\(.value)\(.key)"' "$CONFIG" 2>/dev/null | head -8 | tr '\n' ' ')
  echo "Branch name '$BRANCH' violates convention." >&2
  echo "Pattern: $PATTERN" >&2
  echo "Valid prefixes: $PREFIXES" >&2
  echo "Example: feat/your-feature-name" >&2
  exit 2
fi

exit 0
```

### 4-3. スクリプトを実行可能にする

```bash
chmod +x scripts/hooks/check-branch-convention.sh
```

### 4-4. `.claude/settings.local.json` にフックを追加

`.claude/settings.local.json` を読み取り、`hooks.PreToolUse` 配列に下記エントリを追加する（既存のhooksがあれば配列に追加, `hooks` キーがなければ新規追加）:

```json
{
  "matcher": "Bash",
  "hooks": [
    {
      "type": "command",
      "if": "Bash(git *)",
      "command": "bash \"$CLAUDE_PROJECT_DIR\"/scripts/hooks/check-branch-convention.sh",
      "timeout": 5
    }
  ]
}
```

### 4-5. 完了メッセージ

```
✅ Branch strategy configured:
   Strategy:   <戦略名>
   Deploy flow: <フロー名 or none>
   Config:     .branch-strategy.json
   Hook:       scripts/hooks/check-branch-convention.sh (active)

Next: try creating a branch to test the hook
  git checkout -b feat/my-feature    # ✅ valid
  git checkout -b my-random-branch   # ❌ blocked
```

---

## Phase 5: ブランチ検証（`check`）

### 5-1. 設定を読み込む

```bash
cat .branch-strategy.json
```

`.branch-strategy.json` がない場合: 「`.branch-strategy.json` が見つかりません。先に `/branch-strategy setup` を実行してください」と伝えて終了。

### 5-2. ブランチ一覧を取得して検証

```bash
git branch --list
```

各ブランチを `branchPattern` と照合。protected branches は `OK (protected)` として扱う。

### 5-3. 結果をテーブル表示

```
Branch Convention Check
Strategy: <strategy>  Pattern: <pattern>

  Branch                          Status
  ──────────────────────────────  ──────────────────
  main                            OK (protected)
  feat/add-user-auth              OK
  fix/null-pointer-crash          OK
  my-random-branch                ❌ VIOLATION - no prefix
  feat/x                          ❌ VIOLATION - too short

2 violations out of 5 branches.
```

violation があれば、修正方法の例も示す（例: `git branch -m my-random-branch feat/my-feature`）。

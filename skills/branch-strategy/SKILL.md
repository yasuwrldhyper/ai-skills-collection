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

このスキルは **ブランチ戦略の専門家** として動作する。決定マトリクスで機械的に選ぶのではなく、プロジェクトの状況を理解した上で「なぜこの戦略が適切か」を文脈・根拠と共に提案すること。提案には必ず参考ソース（公式ドキュメント・企業事例）を添えて、思い込みではなく実績ある知見に基づく提案であることを示す。

### 5つの基本戦略

**GitHub Flow**
- ブランチ: `main` + 短命 feature ブランチのみ
- `main` は常にデプロイ可能。feature → PR → `main` のシンプルなフロー
- 適合: 小〜中規模チーム、継続的デプロイ、SaaS プロダクト
- 注意: リリース管理が不要な場合向け。複数バージョン並行は不得意
- 参考: [GitHub Flow 公式ドキュメント](https://docs.github.com/en/get-started/using-github/github-flow)、Scott Chacon (2011) "GitHub Flow"
- 採用例: GitHub 社内、Shopify（+ feature flag）、多くの小〜中規模 SaaS

**Git Flow**
- ブランチ: `main`, `develop`, `feature/*`, `release/*`, `hotfix/*`
- 厳格なマージ規律が必要。`develop` がインテグレーションポイント
- 適合: バージョン管理が必要なソフトウェア、複数バージョン並行メンテ
- 注意: 大規模チームでは `develop` がボトルネックになりマージ競合が頻発。作者自身も「常に正解ではない」と注記
- 参考: Vincent Driessen (2010) "[A successful Git branching model](https://nvie.com/posts/a-successful-git-branching-model/)"
- 採用例: 従来型ソフトウェア開発、パッケージ配布が必要なOSS

**Trunk-based Development**
- ブランチ: `main` + 非常に短命なブランチ（1〜2日で main にマージ）
- feature flag で未完成機能を隠す。高頻度のインテグレーションが前提
- 適合: 高成熟CI/CD 環境、少人数精鋭チーム、高速イテレーション
- 注意: CI/CD が未成熟だと壊れた main が頻発する。feature flag 管理コストも発生
- 参考: Paul Hammant [trunkbaseddevelopment.com](https://trunkbaseddevelopment.com)、Google Engineering Practices
- 採用例: Google（数万人規模のモノレポ）、Meta、Microsoft（一部）、Netflix

**GitLab Flow（環境ブランチ方式）**
- ブランチ: `main` + `staging`, `production` 等の環境ブランチ
- feature → `main` → `staging` → `production` と環境間をマージ昇格
- 適合: 複数のデプロイ環境がある場合、リリース承認フローが必要な場合
- **重大な制約**: 全 feature が同時昇格するため、施策ごとにローンチ時期が異なるモノレポとは相性が最悪
- 参考: [GitLab Flow 公式ドキュメント](https://about.gitlab.com/topics/version-control/what-is-gitlab-flow/)

**Release-branch**
- ブランチ: `main` + `release/vX.Y` の長命リリースブランチ
- 新バージョンは `main` から切り出し、bug fix は cherry-pick で適用
- 適合: バージョンリリース形式だが `develop` ほど複雑なフローが不要な場合
- 参考: [Python](https://devguide.python.org/developer-workflow/development-cycle/)、[Django](https://docs.djangoproject.com/en/dev/internals/release-process/)などの成熟OSSが採用

### デプロイフローオプション

基本戦略の上に重ねて選択する。以下の比較を参考に、ヒアリング内容から適切なものを選ぶ:

| オプション | 適合条件 | 主な制約 |
|----------|---------|---------|
| なし（戦略に準拠） | デプロイはブランチのマージで完結する | — |
| 環境ブランチ方式 | 全機能が同時に各環境を通過する・ポリレポ・単一サービス | モノレポ + 独立ローンチでは全施策一括昇格になり破綻 |
| タグ + デプロイトリガー方式 | 独立した施策/コンポーネントごとにリリース判断が必要・GitHub Releases と連携したい | CI/CD パイプラインにタグトリガーの設定が必要 |

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
承認者が環境間のマージを実施する運用に向く。**ただしモノレポで施策ローンチ時期が独立している場合は禁止**（全施策が一括で昇格してしまう）。

**タグ + デプロイトリガー方式** (`"tag-deploy"`)
```
main（常にデプロイ可能）
  ↑ merge
feat/xxx

タグ付け → GitHub Release 作成 → CI/CD トリガー:
  v1.0.0-rc.1  → QA 環境にデプロイ
  v1.0.0-rc.2  → Staging 環境にデプロイ
  v1.0.0       → 本番デプロイ + GitHub Release（変更内容を記載）
```
GitHub を使っている場合は **GitHub Releases** を活用する:
- タグに対応する Release を作成し、changelog / breaking changes を記録
- `gh release create v1.0.0 --generate-notes` で自動要約も可能
- ステークホルダーへの告知、過去バージョンの参照に使える

モノレポでコンポーネント単位の独立デプロイが必要な場合はタグにプレフィックスを付ける:
```
salesforce/v1.2.0  → salesforce/ ディレクトリ変更のデプロイ
ga4/v0.5.0        → ga4/ ディレクトリ変更のデプロイ
```

### アンチパターン（避けるべき組み合わせ）

| 条件 | アンチパターン | 問題 | 推奨代替 |
|------|--------------|------|---------|
| モノレポ + 施策ごとに独立したローンチ | 環境ブランチ方式 | 全施策が同時昇格。「施策AだけQAに出す」が不可能。リリーストレイン問題 | trunk-based + feature flag、またはタグ方式 |
| モノレポ + 大規模チーム（15人以上） | Git Flow | `develop` が競合のボトルネック。マージ地獄 | trunk-based |
| ポリレポ + マイクロサービス | Git Flow | サービスごとに独立リリースなのにフローが重すぎる | GitHub Flow or trunk-based |
| ソロ / 小規模チーム（〜5人） | Git Flow | オーバーヘッドがメリットを上回る | GitHub Flow |
| CI/CD が手動またはテストが薄い | trunk-based | 壊れたコードが `main` に入りやすい | GitHub Flow（PRで保護） |
| 複数バージョンを同時メンテ | GitHub Flow / trunk-based | リリースブランチの管理が不可能 | Git Flow or release-branch |

### IaC（Terraform等）が含まれる場合の考慮事項

インフラコードが同リポジトリに含まれる場合、以下を判断材料に加える:

**アプリ + Terraform が同一リポジトリの場合:**
- ブランチ戦略はアプリコードと同じで良いが、CI/CD の **パスフィルタ**（`paths: terraform/**`）でインフラ変更時のみ Terraform ワークフローが起動するよう分離する
- Terraform は Plan → Apply の2段階が必要なため、デプロイフローが複雑になりやすい
- データプラットフォームのモノレポでは **コンポーネント（データソース）単位でモジュール分離**すること:
  ```
  terraform/
    modules/
      salesforce/    # salesforce データソース用モジュール
      ga4/           # GA4 データソース用モジュール
      bigquery-export/
    environments/
      dev/
      stg/
      prod/
  ```
  この構造にすると、`paths: terraform/modules/salesforce/**` のパスフィルタでデータソースごとに独立したインフラデプロイが可能になる

**アプリ + Terraform が別リポジトリの場合（推奨）:**
- インフラリポジトリは独立したブランチ戦略を持てる
- アプリのリリースとインフラ変更が分離されるため、それぞれに最適なフロー（例: アプリはGitHub Flow + タグデプロイ、インフラはPR→レビュー→main マージ）を採用できる
- ただしクロスリポジトリの依存関係（APIの変更とインフラの変更を同時にリリースしたい等）の管理が必要

---

## Phase 1: ヒアリング

**目的**: プロジェクトの本質的な特性を把握し、適切な戦略提案に必要な情報を得る。

**重要**: ユーザーが最初のメッセージに情報を書いていても、**必ず AskUserQuestion で対話する**。推論だけで答えに飛びつかないこと。理由は2つある:
1. 明示されていない情報（ローンチ時期の独立性、Terraform の配置、CI/CD 成熟度）が戦略選定を大きく左右する
2. 対話を通じてユーザー自身が気づいていない制約や前提を引き出せる（これが専門家としての価値）

一度に全部聞かず、2ラウンドに分けて段階的に深掘りすること。

### 1-1. 初回ヒアリング

AskUserQuestion で以下を1度に質問する（初回メッセージで既に回答があれば選択肢に「おっしゃる通りです」的な確認を含める形にして良い）:
- プロダクトの種類（Web API / フロントエンド含む Web アプリ / ライブラリ / データ基盤 / モバイルバックエンド / その他）
- リポジトリ構成（モノレポ / ポリレポ / 単一サービス）
- チーム規模（ソロ / 2-5人 / 6-15人 / 15人以上）

### 1-2. 深掘りヒアリング

1-1 の回答を踏まえて、必要な質問のみ追加で聞く。全部聞く必要はない。

以下の観点で情報が不足していれば質問する（1-1 で既に判明した項目はスキップして良い）:
- **モノレポの場合**: 施策・機能のローンチ時期は同期（全機能同時リリース）か独立（機能ごとに別タイミング）か？
- **インフラコード**: Terraform等のIaCはアプリコードと同一リポジトリか別リポジトリか？
- **デプロイ環境**: QA / ステージング / 本番 など何段階あるか？環境ごとに承認フローがあるか？
- **Git ホスティング**: GitHub / GitLab / その他？（GitHub Releases, GitHub Actions 等の機能を活用できるか）
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
6. **デプロイフロー説明** - 採用するデプロイフローのオプション・向き不向きを明示（GitHub を使っている場合は GitHub Releases の活用も提示）
7. **参考ソース** - 採用した戦略の公式ドキュメント・企業事例・実績ある知見を1〜3件引用する
8. **トレードオフと注意点**

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
  "infraRepo": "<same|separate|none>",
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
Infra repo: <same|separate|none>

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

### References
<採用した戦略の参考ソースを記載>
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
MAX_LEN=$(jq -r '.maxBranchNameLength // 60' "$CONFIG")

# Protected branches are always allowed
while IFS= read -r pb; do
  [ "$BRANCH" = "$pb" ] && exit 0
done < <(jq -r '.protectedBranches[]?' "$CONFIG")

# environmentBranches are also exempt from the naming convention
while IFS= read -r eb; do
  [ "$BRANCH" = "$eb" ] && exit 0
done < <(jq -r '.environmentBranches[]?' "$CONFIG")

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
  FIRST_PREFIX=$(jq -r '.branchPrefixes | to_entries[0] | .value' "$CONFIG" 2>/dev/null || echo "feat/")
  echo "Branch name '$BRANCH' violates the convention for this project." >&2
  echo "Required pattern: $PATTERN" >&2
  echo "Example valid name: ${FIRST_PREFIX}your-description" >&2
  echo "Run '/branch-strategy show' to see the full naming convention." >&2
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

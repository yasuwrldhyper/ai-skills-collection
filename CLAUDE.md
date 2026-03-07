# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 概要

AI スキルのサンプルコレクション。バックエンド開発に特化した実装例を収録する。

## ツール管理

- シェル: **zsh**
- バージョン管理: **mise** (`~/.mise.toml` でグローバル設定済み)
- 主なツール: Python (uv), Node.js, AWS CLI, Terraform, jq, biome

新しいランタイムやツールを追加する場合は `mise.toml` に記載する:

```toml
# プロジェクトルートに mise.toml を作成
[tools]
python = "3.12"
node = "22"
```

## コマンド

### 開発環境のセットアップ

```sh
mise install          # 必要なツールをインストール
mise run setup        # プロジェクト初期セットアップ（定義済みの場合）
```

### Python プロジェクト (uv)

```sh
uv sync               # 依存関係のインストール
uv run python main.py # スクリプト実行
uv run pytest         # テスト実行
uv run pytest tests/test_foo.py::test_bar  # 単一テスト実行
uv add <package>      # 依存関係追加
```

### Node.js プロジェクト

```sh
npm install           # 依存関係のインストール
npm run dev           # 開発サーバー起動
npm test              # テスト実行
```

### Lint / Format

```sh
biome check .         # 静的解析
biome format .        # フォーマット
```

## プロジェクト構造

```text
/
├── plan/             # 設計・計画ドキュメント
├── .claude/          # Claude Code 設定
│   └── settings.local.json
├── CLAUDE.md
└── <skill-name>/     # 各スキルのサンプル実装
    ├── README.md
    └── src/
```

各スキルは独立したディレクトリで管理し、それぞれ独自の `mise.toml` や `pyproject.toml` を持つ。

## AWS CLI

get/list 系の操作のみ許可済み（読み取り専用）。書き込み系 (create/delete/update/put) を行う場合は事前に確認を求める。

```sh
aws <service> get-*      # 許可
aws <service> list-*     # 許可
aws <service> describe-* # 許可
```

## 開発方針

- サンプルコードは最小構成で動くことを優先する（余分な抽象化を避ける）
- 各スキルディレクトリには `README.md` で使い方と目的を記載する
- 環境変数は `.env.example` を用意し、`.env` は gitignore に追加する

## AgentTeam（マルチエージェント協調）

### 有効化設定

グローバル（`~/.claude/settings.json`）で設定済みのため、このプロジェクトでは追加設定不要：

- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- `teammateMode: "tmux"`（各チームメイトが独立 tmux ペインで動作）

### 起動条件

**使う：**

- タスクが独立した複数の責務に明確に分割できる場合
- 並列作業でトータル時間を短縮できる場合（目安：3タスク以上が並列化可能）
- 複数の独立した視点が必要な場合（コードレビュー、根本原因調査）

**使わない：**

- 単一の連続した実装タスク（シーケンシャルな依存が多い）
- 小規模な修正・バグフィックス（オーバーヘッドが大きい）
- 既存のサブエージェント（Explore/Plan）で十分な調査・計画タスク

### 制約

- **ファイル競合**: チームメイト間で同一ファイルを同時編集しない。スキルごとに独立ディレクトリを割り当てる
- **チームサイズ**: 通常 3〜5 人。6人以上は調整コストが増大する
- **read-only エージェント**: `Explore` / `Plan` タイプは実装作業を担当できない（ファイル編集ツール非対応）
- **セッション再開**: in-process モードではセッション再開後にチームメイトが復旧しない。新しいチームを spawn する
- **シャットダウン**: 必ず `SendMessage(type: "shutdown_request")` でチームメイトを終了させてから `TeamDelete` を実行する

### ワークフロー

```text
1. TeamCreate        — チームとタスクリストを作成
2. TaskCreate        — タスクを定義（複数）
3. Agent(team_name, name, subagent_type)  — チームメイトを spawn
4. TaskUpdate(owner) — タスクをチームメイトに割り当て
5. ...作業中: SendMessage でチームメイト間コミュニケーション...
6. SendMessage(type: "shutdown_request") — 全チームメイトを終了
7. TeamDelete        — チームリソースをクリーンアップ
```

### チーム構成テンプレート

**パターン1: 研究＋実装分離**（新規スキル実装時）

```text
researcher  : Explore         — 仕様調査・既存実装の収集
implementer : general-purpose — 実装・テスト作成
reviewer    : general-purpose — コードレビュー・README 作成
```

**パターン2: 並列スキル実装**（複数スキルを同時開発）

```text
skill-{name1} : general-purpose — {skill-name1}/ ディレクトリ担当
skill-{name2} : general-purpose — {skill-name2}/ ディレクトリ担当
skill-{name3} : general-purpose — {skill-name3}/ ディレクトリ担当
```

**パターン3: 競合仮説バグ調査**（根本原因不明のバグ）

```text
仮説ごとにチームメイトを spawn（3〜5人）
各自が独立して検証し、SendMessage で議論して収束
```

**パターン4: 並列コードレビュー**（多角的品質チェック）

```text
sec-reviewer   : general-purpose — セキュリティ視点
perf-reviewer  : general-purpose — パフォーマンス視点
test-reviewer  : general-purpose — テストカバレッジ視点
```

### ファイル責務分離

```text
src/api/        → API チームメイト
src/db/         → DB チームメイト
tests/          → テスト チームメイト
{skill-name}/   → skill-{name} チームメイト（各スキルは独立ディレクトリ）
```

## 利用可能なスキル

プロジェクトローカル（`.claude/skills/`）に以下のスキルがインストール済み。スラッシュコマンドで起動する。

### 独自スキル

| コマンド | 説明 |
| --- | --- |
| `/code-review <path>` | 5人の専門家エージェントが並列でコードレビューを実施し、`.claude/reviews/` にレポートを保存 |
| `/gcp-expert [質問]` | GCP サービス選定・実装パターン・セキュリティベストプラクティスをアドバイス |
| `/generate-ci [path]` | 言語・IaC を自動検出し、GitHub Actions CI ワークフローをベストプラクティス（SHA固定・最小権限・カバレッジ可視化・シークレットスキャン）に基づいて対話的に生成 |

### コミュニティスキル（skills.sh 経由）

| コマンド | 説明 | 出典 |
| --- | --- | --- |
| `/systematic-debugging` | 4フェーズの体系的デバッグ（根本原因調査→パターン分析→仮説検証→実装） | obra/superpowers |
| `/git-commit` | Conventional Commits 仕様に基づいたコミットメッセージを自動生成 | github/awesome-copilot |
| `/requesting-code-review` | コードレビュー依頼を自動化・優先度分類（Critical/Important/Minor） | obra/superpowers |
| `/gh-cli` | GitHub CLI の包括的リファレンス（PR・Issue・Actions 等） | github/awesome-copilot |
| `/skill-creator` | 新しいスキルの SKILL.md を対話的に生成・改善 | anthropics/skills |

### スキルの管理

```sh
npx skills list      # インストール済みスキル一覧
npx skills update    # 全スキルを最新版に更新
npx skills check     # アップデート確認
npx skills add <owner/repo@skill>  # 新規スキルを追加
```

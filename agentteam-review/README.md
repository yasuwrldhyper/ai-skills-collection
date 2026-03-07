# agentteam-review

AgentTeam を使った **並列コードレビュー** のサンプル実装。
5人の専門家エージェントがそれぞれのペルソナで並列レビューを行い、統合レポートを生成する。

## 概要

`/code-review` スキルを実行すると、以下の専門家エージェントが同時にコードを分析する:

| エージェント | ペルソナ | モデル | 主な観点 |
|-------------|---------|-------|---------|
| `python-specialist` | Python コア開発者・PEP 作者水準 | Sonnet | Pythonic・型ヒント・パフォーマンス・セキュリティ |
| `test-specialist` | t-wada（和田卓人）型 TDD 権威 | Haiku | テスタビリティ・境界値・副作用の分離 |
| `architect` | SOLID/DRY/Clean Architecture 専門家 | Sonnet | 神クラス・DRY違反・依存性逆転・OCP |
| `aws-specialist` | AWS 認定ソリューションアーキテクト | Haiku | IAM最小権限・S3セキュリティ・boto3パターン |
| `gcp-specialist` | Google Cloud 認定アーキテクト | Haiku | ADC・Secret Manager・GCS セキュリティ |

**モデル選択基準**: 抽象的推論が必要な専門家（Python・アーキテクト）は Sonnet、チェックリスト的分析が中心の専門家（テスト・AWS・GCP）は Haiku を使用し、コストと品質のバランスを取る。

## 使い方

```sh
# 1. セットアップ
cd agentteam-review
mise install
uv sync

# 2. 環境変数の設定
cp .env.example .env

# 3. Claude Code でリポジトリルートから実行
# スキルは .claude/skills/code-review/SKILL.md に配置済み
/code-review agentteam-review/src/sample_app/
```

レビューレポートは `.claude/reviews/code-review-{timestamp}.md` に自動保存される。

## サンプルコード（レビュー対象）

`src/sample_app/` には **意図的に問題を含んだ** サンプルコードが入っている:

| ファイル | 含まれる問題 |
|---------|------------|
| `api.py` | SQLインジェクション・ハードコードシークレット・N+1クエリ・型ヒントなし |
| `storage.py` | AWS/GCP認証情報ハードコード・過剰IAM権限・リソースリーク |
| `utils.py` | 神クラス（SRP違反）・DRY違反・`time.sleep`混入・OCP違反 |

## `/simplify` との比較・推奨フロー

| 項目 | `/simplify` | `/code-review` |
|------|------------|---------------|
| 目的 | コードを実際に修正する | 専門家視点でレビューレポートを生成 |
| エージェント構成 | コード再利用・品質・効率性の3視点 | Python/テスト/設計/AWS/GCPの専門家5人 |
| 出力 | 修正されたコード | Markdown レビューレポート |
| 発見できる問題 | コードの非効率・重複・品質 | クラウド固有・TDD設計・SOLID違反などドメイン固有の深い問題 |
| 適した場面 | 実装後のクリーンアップ | コミット前の多角的品質チェック |

### 推奨フロー

```
1. /simplify         — 基本的なコード品質の問題を自動修正
         ↓
2. /code-review <path> — より深いドメイン固有の問題を専門家視点で発見
```

`/simplify` では発見・修正しにくい問題（IAM設計・テスタビリティ・SOLID原則違反）を `/code-review` で深堀りする。

## AgentTeam の動作フロー

```
/code-review src/sample_app/
        |
        ├── TeamCreate "code-review"
        ├── TaskCreate × 5
        |
        ├── [並列 spawn]
        |   ├── Agent: python-specialist  (sonnet)
        |   ├── Agent: test-specialist    (haiku)
        |   ├── Agent: architect          (sonnet)
        |   ├── Agent: aws-specialist     (haiku)
        |   └── Agent: gcp-specialist     (haiku)
        |
        ├── [並列レビュー実行]
        |   └── 各エージェントが src/sample_app/ を独立分析
        |
        ├── 統合レポート生成 → .claude/reviews/ に保存
        |   ├── エグゼクティブサマリー
        |   ├── 優先対応事項 TOP 5（横断的）
        |   └── 各専門家の詳細レポート
        |
        └── クリーンアップ（shutdown → TeamDelete）
```

## スキルの配置

スキル本体は **リポジトリルートの** `.claude/skills/code-review/SKILL.md` に配置されている。
リポジトリルートで Claude Code を開いていれば `/code-review` コマンドが使用可能。

## 前提条件

- Claude Code で AgentTeam が有効（`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`）
- tmux がインストール済み（`teammateMode: "tmux"` の場合）
- Python 3.12+（mise で管理）

AgentTeam の設定はグローバル（`~/.claude/settings.json`）で済んでいる前提のため、このプロジェクトに追加設定は不要。

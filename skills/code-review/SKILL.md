---
name: code-review
description: AgentTeamを使って専門家ペルソナの並列コードレビューを行う。Python/テスト/設計原則/AWS/GCPの各スペシャリストが多角的にレビューし、統合レポートを出力する。/simplifyより深いドメイン固有の問題を発見する。
argument-hint: <review-target-path>
disable-model-invocation: true
allowed-tools: TeamCreate, TaskCreate, TaskUpdate, TaskGet, TaskList, SendMessage, TeamDelete, Read, Glob, Agent, Write
---

# /code-review スキル

引数 `$ARGUMENTS` で指定されたパスのコードを、5人の専門家エージェントが並列でレビューし、統合レポートを `.claude/reviews/` に Markdown ファイルとして保存する。

## Phase 1: セットアップ

### 1-1. チームとタスクの作成

以下の手順でチームとタスクを作成する（TeamCreate → TaskCreate × 5）:

```
TeamCreate: チーム名 "code-review"

TaskCreate × 5:
  - title: "Python品質レビュー",      description: "Pythonic・型ヒント・パフォーマンス・標準ライブラリ活用の観点でレビュー"
  - title: "テスト設計レビュー",      description: "テスタビリティ・境界値・TDD設計・テスト困難な実装の検出"
  - title: "アーキテクチャレビュー",  description: "SOLID原則・DRY違反・Clean Architecture・過剰結合の検出"
  - title: "AWSレビュー",             description: "IAM最小権限・Well-Architected・SDK使用パターン・コスト最適化"
  - title: "GCPレビュー",             description: "GCPベストプラクティス・クライアントライブラリ・認証・リソース管理"
```

### 1-2. エージェントの spawn

以下の5エージェントを **並列で** spawn する（Agent ツールを5回同時呼び出し）。
**モデル選択基準**: 抽象的推論が必要 → Sonnet、チェックリスト的分析 → Haiku

**python-specialist**（チーム: code-review, タイプ: general-purpose, **モデル: sonnet**）

初期メッセージ:
```
あなたは Python コア開発者・PEP 作者水準の Python スペシャリストです。
担当タスクが割り当てられたら、指定されたコードを以下の観点でレビューしてください:

【レビュー観点】
- Pythonic なコードか（リスト内包表記・ジェネレーター・with文の活用）
- 型ヒント（Type Hints）の有無と正確さ
- パフォーマンスの問題（不要なループ・メモリ効率・遅延評価の欠如）
- 標準ライブラリの活用（車輪の再発明がないか）
- 例外処理の適切さ
- セキュリティ問題（SQLインジェクション・ハードコードシークレット等）

【制約】
- AWS/GCP固有の設計問題はaws-specialist/gcp-specialistの担当なので言及しない
- テスト設計・アーキテクチャの深い議論は他の専門家に委ねる

レビュー完了後、SendMessage で結果をオーケストレーター（コーディネーター）に送信してください。
タスクの完了をTaskUpdateで記録することを忘れずに。
```

**test-specialist**（チーム: code-review, タイプ: general-purpose, **モデル: haiku**）

初期メッセージ:
```
あなたは t-wada（和田卓人）スタイルの TDD 権威・テスト設計スペシャリストです。
担当タスクが割り当てられたら、指定されたコードを以下の観点でレビューしてください:

【レビュー観点】
- テストコードの存在と品質（ユニットテスト・統合テスト）
- テスタビリティ（依存性注入・モック可能性・副作用の分離）
- テスト困難な実装の検出（time.sleep・ハードコード外部依存・グローバル状態）
- 境界値・異常系のカバレッジ
- TDD 観点での設計評価（テストから設計を逆算できるか）
- テストダブル（モック・スタブ・スパイ）の適切な活用

【制約】
- Python 言語機能の詳細はpython-specialistの担当
- アーキテクチャ全般はarchitectの担当

レビュー完了後、SendMessage で結果をオーケストレーター（コーディネーター）に送信してください。
タスクの完了をTaskUpdateで記録することを忘れずに。
```

**architect**（チーム: code-review, タイプ: general-purpose, **モデル: sonnet**）

初期メッセージ:
```
あなたは SOLID原則・DRY・Clean Architecture の権威・ソフトウェアアーキテクト専門家です。
担当タスクが割り当てられたら、指定されたコードを以下の観点でレビューしてください:

【レビュー観点】
- 単一責任原則（SRP）: クラス・関数が単一の責務を持つか
- 開放閉鎖原則（OCP）: 拡張に開き・修正に閉じているか（条件分岐による機能追加はNG）
- リスコフ置換原則（LSP）: サブクラスが親クラスと置換可能か
- インターフェイス分離原則（ISP）: 不要なインターフェイスへの依存がないか
- 依存性逆転原則（DIP）: 上位モジュールが下位モジュールに依存していないか
- DRY（Don't Repeat Yourself）: コードの重複・コピペの検出
- 過剰な結合（Tight Coupling）: 直接インスタンス化・グローバル依存
- 神クラス（God Class）: 過剰な責務を持つクラスの検出

【制約】
- クラウド固有の設計はaws-specialist/gcp-specialistの担当
- Python言語の詳細はpython-specialistの担当

レビュー完了後、SendMessage で結果をオーケストレーター（コーディネーター）に送信してください。
タスクの完了をTaskUpdateで記録することを忘れずに。
```

**aws-specialist**（チーム: code-review, タイプ: general-purpose, **モデル: haiku**）

初期メッセージ:
```
あなたは AWS 認定ソリューションアーキテクト（SAP・SAA）資格を持つ AWS エキスパートです。
担当タスクが割り当てられたら、指定されたコードを以下の観点でレビューしてください:

【レビュー観点】
- IAM 最小権限の原則: ハードコードされた認証情報・過剰なポリシー
- AWS Well-Architected Framework: セキュリティ・信頼性・パフォーマンス効率・コスト最適化
- boto3 の使用パターン: クライアント再利用・セッション管理・ページネーター
- S3 セキュリティ: パブリックアクセス・バケットポリシー・暗号化・バージョニング
- エラーハンドリング: リトライ戦略・指数バックオフ・botocore.exceptions の活用
- コスト最適化: 不要な API コール・ストレージクラスの選択
- リソースリーク: クライアントのライフサイクル管理

【制約】
- GCP固有の問題はgcp-specialistの担当なので言及しない
- 汎用的なPythonコードの問題はpython-specialistの担当

レビュー完了後、SendMessage で結果をオーケストレーター（コーディネーター）に送信してください。
タスクの完了をTaskUpdateで記録することを忘れずに。
```

**gcp-specialist**（チーム: code-review, タイプ: general-purpose, **モデル: haiku**）

初期メッセージ:
```
あなたは Google Cloud 認定クラウドアーキテクト・Professional Data Engineer 資格を持つ GCP エキスパートです。
担当タスクが割り当てられたら、指定されたコードを以下の観点でレビューしてください:

【レビュー観点】
- GCP 認証: Application Default Credentials（ADC）の使用・サービスアカウントキーの管理
- Google Cloud クライアントライブラリのベストプラクティス（再試行・タイムアウト）
- IAM 最小権限: 必要最小限のスコープ・役割の使用
- Secret Manager: シークレットのハードコードではなく Secret Manager の使用
- GCS セキュリティ: 均一バケットレベルのアクセス・暗号化・ライフサイクルポリシー
- リソース管理: クライアントのコンテキストマネージャー使用・接続プーリング
- エラーハンドリング: google.api_core.exceptions の活用・リトライ設定

【制約】
- AWS固有の問題はaws-specialistの担当なので言及しない
- 汎用的なPythonコードの問題はpython-specialistの担当

レビュー完了後、SendMessage で結果をオーケストレーター（コーディネーター）に送信してください。
タスクの完了をTaskUpdateで記録することを忘れずに。
```

### 1-3. タスクの割り当て

各エージェントが spawn されたら、TaskUpdate で各タスクのオーナーを設定する:
- "Python品質レビュー" → python-specialist
- "テスト設計レビュー" → test-specialist
- "アーキテクチャレビュー" → architect
- "AWSレビュー" → aws-specialist
- "GCPレビュー" → gcp-specialist

## Phase 2: 並列レビューの実行

### 2-1. レビュー指示の送信

全エージェントに対して、以下の内容で SendMessage を送信する（並列送信可）:

```
レビュー対象: $ARGUMENTS

以下のファイルを担当の専門領域の観点でレビューしてください:
- src/sample_app/api.py
- src/sample_app/storage.py
- src/sample_app/utils.py

各ファイルを Read ツールで読み込み、あなたの専門領域に関連する問題点を
以下のフォーマットで報告してください:

## [専門家名] レビュー結果

### 発見した問題点

| 深刻度 | ファイル | 行番号付近 | 問題の概要 |
|--------|---------|-----------|-----------|
| CRITICAL | ... | ... | ... |
| HIGH | ... | ... | ... |
| MEDIUM | ... | ... | ... |
| LOW | ... | ... | ... |

### 詳細説明

（各問題の詳細と改善案）

### 総評

（総括コメント）
```

### 2-2. 完了待機

TaskList でチーム "code-review" のタスク一覧を確認し、全タスクが `completed` になるまで待機する。
進捗は適宜 TaskList で確認すること。

## Phase 3: 統合レポートの生成とファイル保存

5人のエージェントからのレビュー結果（SendMessage 受信）を統合し、以下の形式でレポートを生成する。
生成後、Write ツールで `.claude/reviews/code-review-{YYYYMMDD-HHMMSS}.md` に保存する。

**重要**: ファイル名にはタイムスタンプを含め、複数回実行しても上書きされないようにすること。

---

# コードレビュー統合レポート

**レビュー対象**: `$ARGUMENTS`
**レビュー実施日**: （現在日時）
**レビュアー**: Python Specialist (sonnet) / Test Specialist (haiku) / Architect (sonnet) / AWS Specialist (haiku) / GCP Specialist (haiku)

---

## エグゼクティブサマリー

（全体的な品質評価と主要な問題点の要約）

## 優先対応事項 TOP 5

（5視点を横断した最も重要な問題を優先度順に列挙）

1. **[CRITICAL]** ...（担当: aws-specialist）
2. **[CRITICAL]** ...（担当: python-specialist）
3. **[HIGH]** ...（担当: architect）
4. **[HIGH]** ...（担当: gcp-specialist）
5. **[HIGH]** ...（担当: test-specialist）

---

## 各専門家レビュー

### Python スペシャリスト

（python-specialist の結果をそのまま掲載）

### テスト設計スペシャリスト

（test-specialist の結果をそのまま掲載）

### アーキテクトスペシャリスト

（architect の結果をそのまま掲載）

### AWS スペシャリスト

（aws-specialist の結果をそのまま掲載）

### GCP スペシャリスト

（gcp-specialist の結果をそのまま掲載）

---

## 改善ロードマップ

### 即座に対応が必要（CRITICAL）
（全専門家の CRITICAL 問題をまとめる）

### 優先的に対応（HIGH）
（全専門家の HIGH 問題をまとめる）

### 余裕があれば対応（MEDIUM/LOW）
（MEDIUM・LOW 問題の概要）

---

## Phase 4: クリーンアップ

全タスクが完了し統合レポートをファイル保存したら、以下の順序でクリーンアップを実行する:

1. 全エージェントに `SendMessage(type: "shutdown_request")` を送信
2. 全エージェントのシャットダウンを確認
3. `TeamDelete` でチーム "code-review" を削除
4. 保存したレポートファイルのパスをユーザーに通知する

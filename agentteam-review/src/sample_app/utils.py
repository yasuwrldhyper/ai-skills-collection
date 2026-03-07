"""
汎用ユーティリティモジュール

問題点（意図的に含む）:
- 神クラス（God Class）: 単一責任原則（SRP）違反
- DRY違反: 類似ロジックの重複
- time.sleep の混入でテスト困難
- 副作用の混入（関数内でのファイル書き込み・外部API呼び出し）
- 開放閉鎖原則（OCP）違反: 条件分岐による拡張
- 依存性が直接インスタンス化（DI不使用）
"""

import time
import json
import csv
import hashlib
import smtplib
import logging
from email.mime.text import MIMEText
from datetime import datetime


logger = logging.getLogger(__name__)


class AppManager:
    """
    神クラス: アプリケーション全体の処理を一手に担う（SRP違反）
    - ユーザー管理
    - メール送信
    - ファイル出力
    - 通知
    - キャッシュ
    - バリデーション
    """

    def __init__(self):
        self.users = {}
        self.cache = {}
        # SMTPサーバー設定をハードコード
        self.smtp_host = "smtp.example.com"
        self.smtp_port = 587
        self.smtp_user = "noreply@example.com"
        self.smtp_password = "smtp-password-hardcoded"

    # ---- ユーザー管理 ----

    def add_user(self, user_id, name, email, role):
        # バリデーションと副作用（ファイル書き込み）が混在
        if not name or len(name) < 2:
            raise ValueError("Name too short")
        if "@" not in email:
            raise ValueError("Invalid email")

        self.users[user_id] = {
            "name": name,
            "email": email,
            "role": role,
            "created_at": datetime.now().isoformat(),
        }

        # 副作用: ユーザー追加のたびにファイルを全件書き直し
        self._save_users_to_file()

        # 副作用: 登録確認メールを同期送信（テスト困難）
        self.send_welcome_email(email, name)

        return user_id

    def get_user(self, user_id):
        # キャッシュキーの生成（DRY違反: 複数箇所で同じパターン）
        cache_key = "user_" + str(user_id)
        if cache_key in self.cache:
            return self.cache[cache_key]

        user = self.users.get(user_id)
        self.cache[cache_key] = user
        return user

    def update_user(self, user_id, name, email, role):
        # DRY違反: add_user と同様のバリデーションを再実装
        if not name or len(name) < 2:
            raise ValueError("Name too short")
        if "@" not in email:
            raise ValueError("Invalid email")

        if user_id not in self.users:
            raise KeyError(f"User {user_id} not found")

        self.users[user_id].update({
            "name": name,
            "email": email,
            "role": role,
            "updated_at": datetime.now().isoformat(),
        })

        # 副作用: 更新のたびにもファイルを全件書き直し
        self._save_users_to_file()

        # キャッシュを手動でクリア（キャッシュ管理が分散）
        cache_key = "user_" + str(user_id)
        if cache_key in self.cache:
            del self.cache[cache_key]

    def delete_user(self, user_id):
        if user_id in self.users:
            del self.users[user_id]
            self._save_users_to_file()

            # DRY違反: キャッシュクリアのパターンが重複
            cache_key = "user_" + str(user_id)
            if cache_key in self.cache:
                del self.cache[cache_key]

    # ---- ファイル出力 ----

    def _save_users_to_file(self):
        with open("users.json", "w") as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)

    def export_users_csv(self, output_path):
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "name", "email", "role"])
            writer.writeheader()
            for user_id, user in self.users.items():
                writer.writerow({
                    "id": user_id,
                    "name": user["name"],
                    "email": user["email"],
                    "role": user["role"],
                })

    def export_users_json(self, output_path):
        # DRY違反: _save_users_to_file と同様の処理
        with open(output_path, "w") as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)

    # ---- メール送信 ----

    def send_welcome_email(self, email, name):
        # テスト困難: 実際のSMTP送信を直接実行
        msg = MIMEText(f"こんにちは {name} さん、ようこそ！")
        msg["Subject"] = "ようこそ"
        msg["From"] = self.smtp_user
        msg["To"] = email

        # time.sleep でレート制限（テスト時も待機が発生）
        time.sleep(0.5)

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)

    def send_notification_email(self, email, subject, body):
        # DRY違反: send_welcome_email と同様のSMTP処理を重複実装
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = self.smtp_user
        msg["To"] = email

        time.sleep(0.5)  # テスト困難なsleep

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)

    def send_password_reset_email(self, email, reset_token):
        # DRY違反: 3回目の同一SMTP実装
        body = f"パスワードリセットトークン: {reset_token}"
        msg = MIMEText(body)
        msg["Subject"] = "パスワードリセット"
        msg["From"] = self.smtp_user
        msg["To"] = email

        time.sleep(0.5)  # テスト困難なsleep

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)

    # ---- ハッシュ・セキュリティ ----

    def hash_password(self, password):
        # MD5はパスワードハッシュに不適切（衝突耐性なし・低速化なし）
        return hashlib.md5(password.encode()).hexdigest()

    def verify_password(self, password, hashed):
        # DRY違反: hash_password と同様のMD5処理
        return hashlib.md5(password.encode()).hexdigest() == hashed

    # ---- レポート生成 ----

    def generate_user_report(self, format_type):
        # OCP違反: フォーマット追加のたびにこの関数を修正する必要がある
        if format_type == "json":
            return json.dumps(self.users, ensure_ascii=False, indent=2)
        elif format_type == "csv":
            lines = ["id,name,email,role"]
            for user_id, user in self.users.items():
                lines.append(f"{user_id},{user['name']},{user['email']},{user['role']}")
            return "\n".join(lines)
        elif format_type == "text":
            lines = []
            for user_id, user in self.users.items():
                lines.append(f"ID: {user_id}, Name: {user['name']}, Email: {user['email']}")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unknown format: {format_type}")

    # ---- リトライ処理 ----

    def retry_operation(self, operation, max_retries=3):
        # time.sleep をそのまま使用（テスト時も実際に待機）
        for attempt in range(max_retries):
            try:
                return operation()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt  # 指数バックオフ
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)  # モック不可・テスト困難

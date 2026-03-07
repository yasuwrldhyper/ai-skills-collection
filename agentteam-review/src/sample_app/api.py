"""
ユーザー管理 API モジュール

問題点（意図的に含む）:
- SQLインジェクション脆弱性（文字列結合でSQL構築）
- ハードコードされたシークレット
- N+1クエリ問題
- 型ヒントなし
- エラーハンドリング不足
"""

import sqlite3

# ハードコードされたシークレット（セキュリティ問題）
API_SECRET = "super-secret-key-12345"
DB_PATH = "app.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def get_user(username):
    conn = get_connection()
    # SQLインジェクション脆弱性: ユーザー入力を直接文字列結合
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor = conn.cursor()
    result = cursor.fetchone()
    conn.close()
    return result


def get_all_users_with_orders():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()

    result = []
    # N+1クエリ問題: ユーザーごとに別途DBクエリを発行
    for user in users:
        cursor.execute("SELECT * FROM orders WHERE user_id = " + str(user[0]))
        orders = cursor.fetchall()
        result.append({"user": user, "orders": orders})

    conn.close()
    return result


def create_user(username, email, password):
    conn = get_connection()
    cursor = conn.cursor()
    # パスワードを平文で保存
    cursor.execute(
        "INSERT INTO users (username, email, password) VALUES ('"
        + username
        + "', '"
        + email
        + "', '"
        + password
        + "')"
    )
    conn.commit()
    conn.close()


def search_users(keyword):
    conn = get_connection()
    cursor = conn.cursor()
    # SQLインジェクション（LIKE句でも同様の問題）
    query = f"SELECT * FROM users WHERE username LIKE '%{keyword}%' OR email LIKE '%{keyword}%'"
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results


def authenticate(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    # タイミング攻撃に脆弱な認証（文字列比較）
    cursor.execute(
        "SELECT * FROM users WHERE username = '"
        + username
        + "' AND password = '"
        + password
        + "'"
    )
    user = cursor.fetchone()
    conn.close()
    if user:
        # シークレットをそのままトークンとして使用
        return API_SECRET + ":" + username
    return None


def delete_user(username):
    conn = get_connection()
    cursor = conn.cursor()
    # SQLインジェクション（DELETE文）
    cursor.execute("DELETE FROM users WHERE username = '" + username + "'")
    conn.commit()
    conn.close()

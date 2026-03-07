"""
クラウドストレージモジュール（AWS S3 + GCP GCS）

問題点（意図的に含む）:
- ハードコードされた認証情報（AWS・GCP）
- 過剰なIAM権限（AdministratorAccess相当のポリシー）
- リソースリーク（クライアントのクローズなし）
- GCP: Application Default Credentials を使わずキーをハードコード
- AWS: リージョンハードコード・バケット名ハードコード
- エラー時のリトライなし
"""

import boto3
import json
from google.cloud import storage as gcs
from google.oauth2 import service_account


# ハードコードされたAWS認証情報（セキュリティ問題）
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
AWS_REGION = "ap-northeast-1"
S3_BUCKET = "my-app-bucket-prod"

# ハードコードされたGCPサービスアカウントキー（セキュリティ問題）
GCP_SERVICE_ACCOUNT = {
    "type": "service_account",
    "project_id": "my-project-12345",
    "private_key_id": "key-id-example",
    "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAK...\n-----END RSA PRIVATE KEY-----\n",
    "client_email": "myapp@my-project-12345.iam.gserviceaccount.com",
    "client_id": "123456789",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
}
GCS_BUCKET = "my-app-gcs-bucket"


def get_s3_client():
    # 過剰権限: AdministratorAccess 相当のキーを使用
    # クライアントを毎回生成（接続プーリングなし）
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )


def get_gcs_client():
    # ハードコードされたサービスアカウントキーで認証
    credentials = service_account.Credentials.from_service_account_info(
        GCP_SERVICE_ACCOUNT,
        # 全スコープを要求（最小権限の原則違反）
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    return gcs.Client(project="my-project-12345", credentials=credentials)


def upload_to_s3(file_path, object_key):
    # リソースリーク: 例外時にクライアントが解放されない
    client = get_s3_client()
    client.upload_file(file_path, S3_BUCKET, object_key)
    # クライアントのクローズ処理なし


def download_from_s3(object_key, dest_path):
    client = get_s3_client()
    client.download_file(S3_BUCKET, object_key, dest_path)


def list_s3_objects(prefix=""):
    client = get_s3_client()
    # ページネーションなし（大量オブジェクト時に途中で切れる）
    response = client.list_objects_v2(Bucket=S3_BUCKET, Prefix=prefix)
    return response.get("Contents", [])


def delete_s3_object(object_key):
    client = get_s3_client()
    # 削除前の存在確認なし・バージョニング考慮なし
    client.delete_object(Bucket=S3_BUCKET, Key=object_key)


def upload_to_gcs(file_path, blob_name):
    # リソースリーク: GCSクライアントのクローズなし
    client = get_gcs_client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(file_path)
    # クライアントのクローズ処理なし


def download_from_gcs(blob_name, dest_path):
    client = get_gcs_client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(dest_path)


def copy_s3_to_gcs(s3_key, gcs_blob_name):
    # 一時ファイルを使った非効率な転送（ストリーミング不使用）
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name

    download_from_s3(s3_key, tmp_path)
    upload_to_gcs(tmp_path, gcs_blob_name)
    os.unlink(tmp_path)


def create_s3_bucket(bucket_name, region=None):
    client = get_s3_client()
    # パブリックアクセスブロックを設定しないままバケット作成
    if region:
        client.create_bucket(
            Bucket=bucket_name,
            CreateBucketConfiguration={"LocationConstraint": region},
        )
    else:
        client.create_bucket(Bucket=bucket_name)
    # バケットポリシー・暗号化設定なし


def grant_s3_public_read(object_key):
    client = get_s3_client()
    # オブジェクトをパブリック公開（データ漏洩リスク）
    client.put_object_acl(
        Bucket=S3_BUCKET,
        Key=object_key,
        ACL="public-read",
    )

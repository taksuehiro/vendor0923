# backend/rag_core_s3.py
import os, io, json, time, hashlib, boto3
from botocore.exceptions import ClientError

BUCKET = os.getenv("VECTORSTORE_S3_BUCKET")
PREFIX = os.getenv("VECTORSTORE_S3_PREFIX", "vectorstore/prod")
CURRENT = f"{PREFIX}/current"
STAGING = f"{PREFIX}/staging"

_s3 = boto3.client("s3")

def _s3_key(key: str) -> str:
    return key if not key.startswith("/") else key[1:]

def exists_current() -> bool:
    try:
        _s3.list_objects_v2(Bucket=BUCKET, Prefix=f"{CURRENT}/", MaxKeys=1)
        resp = _s3.list_objects_v2(Bucket=BUCKET, Prefix=f"{CURRENT}/index.faiss", MaxKeys=1)
        return resp.get("KeyCount", 0) > 0
    except ClientError:
        return False

def download_current_to(local_dir: str):
    os.makedirs(local_dir, exist_ok=True)
    for key in ["index.faiss", "index.pkl"]:
        src = f"{CURRENT}/{key}"
        try:
            _s3.download_file(BUCKET, _s3_key(src), os.path.join(local_dir, key))
        except ClientError as e:
            raise RuntimeError(f"S3 download failed: {src} ({e})")

def upload_to_staging(local_dir: str) -> str:
    ts = int(time.time())
    base = f"{STAGING}/{ts}"
    for key in ["index.faiss", "index.pkl"]:
        _s3.upload_file(
            os.path.join(local_dir, key), BUCKET, _s3_key(f"{base}/{key}")
        )
    return base  # staging prefix

def promote_staging_to_current(staging_prefix: str):
    # "current/"を丸ごと差し替え（コピー & 旧current上書き）
    # index.faiss / index.pkl の2ファイル想定
    for key in ["index.faiss", "index.pkl"]:
        _s3.copy_object(
            Bucket=BUCKET,
            CopySource={"Bucket": BUCKET, "Key": _s3_key(f"{staging_prefix}/{key}")},
            Key=_s3_key(f"{CURRENT}/{key}"),
        )

def ensure_vectorstore_local(local_dir: str):
    """
    Backward compatibility alias.
    Previously, main.py expected ensure_vectorstore_local().
    This simply calls download_current_to().
    """
    return download_current_to(local_dir)
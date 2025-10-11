# backend/vectorstore.py
import os
import tempfile
import shutil
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from langchain_community.vectorstores import FAISS

# ==== 環境変数（統一＆後方互換） ============================================
# 推奨：S3_BUCKET_NAME / S3_PREFIX を正とする（旧名もフォールバック）
S3_BUCKET = os.environ.get("S3_BUCKET_NAME") or os.environ.get("S3_BUCKET") or "vendor-rag-0919"
S3_PREFIX = os.environ.get("S3_PREFIX") or os.environ.get("VECTORSTORE_S3_PREFIX") or "vectorstore/prod"

AWS_REGION = os.environ.get("AWS_REGION", "ap-northeast-1")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", AWS_REGION)

# 推奨：BEDROCK_EMBEDDINGS_MODEL_ID を正とする（旧名もフォールバック）
# デフォルトは v1（:0 などのサフィックスは除去して使う）
RAW_MODEL_ID = (
    os.environ.get("BEDROCK_EMBEDDINGS_MODEL_ID")
    or os.environ.get("BEDROCK_EMBED_MODEL")
    or "amazon.titan-embed-text-v1"
)

def _normalize_model_id(raw: str) -> str:
    # v2:0 等のサフィックスが来ても : 以降を切り捨てる
    return raw.split(":")[0].strip()

EMBED_MODEL_ID = _normalize_model_id(RAW_MODEL_ID)

# ==== 互換ラッパー（方式A） ================================================
from langchain_community.embeddings import BedrockEmbeddings as _LCBedrockEmbeddings

class BedrockEmbeddingsCompat(_LCBedrockEmbeddings):
    """FAISSや旧コードが callable 前提でも動くようにする互換ラッパー"""
    def __call__(self, text: str):
        return self.embed_query(text)

# ==== グローバルキャッシュ ===================================================
VSTORE = None

def _init_embeddings() -> BedrockEmbeddingsCompat:
    """互換ラッパー付きの BedrockEmbeddings（V1）で初期化"""
    return BedrockEmbeddingsCompat(
        model_id=EMBED_MODEL_ID,      # 例: amazon.titan-embed-text-v1
        region_name=BEDROCK_REGION,   # 例: ap-northeast-1
    )

def load_vectorstore():
    """
    S3からFAISSインデックスをダウンロードしてロードする

    Returns:
        FAISS: ロードされたベクトルストア
    """
    global VSTORE
    if VSTORE is not None:
        return VSTORE

    s3 = boto3.resource("s3", region_name=AWS_REGION)
    bucket = s3.Bucket(S3_BUCKET)

    # 一時ディレクトリ（終了時にクリーンアップ）
    tmpdir = tempfile.mkdtemp(prefix="faiss_")
    local_dir = os.path.join(tmpdir, "faiss")
    os.makedirs(local_dir, exist_ok=True)

    try:
        # --- S3 から同期 ---
        prefix = S3_PREFIX.rstrip("/") + "/"
        for obj in bucket.objects.filter(Prefix=prefix):
            rel = obj.key[len(prefix):]
            if not rel or rel.endswith("/"):
                continue
            dst_path = os.path.join(local_dir, rel)
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            bucket.download_file(obj.key, dst_path)

        # --- FAISS ロード（V1 Embeddings を渡す）---
        emb = _init_embeddings()
        VSTORE = FAISS.load_local(
            folder_path=local_dir,
            embeddings=emb,
            allow_dangerous_deserialization=True,
        )
        # 念のためembedding_functionを明示上書き（方式B：安全策）
        VSTORE.embedding_function = emb.embed_query
        return VSTORE

    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3 download error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FAISS load error: {e}")
    finally:
        # 一時ディレクトリを必ず削除
        shutil.rmtree(tmpdir, ignore_errors=True)

# backend/rag_core/core.py
import logging
import os
import traceback
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import BedrockEmbeddings
from . import __init__  # noqa: F401
from backend.rag_core_s3 import ensure_vectorstore_local

log = logging.getLogger(__name__)

def _env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)

def _resolve_bucket_prefix():
    # 正: S3_BUCKET_NAME / S3_PREFIX
    # 後方互換: VECTORSTORE_S3_BUCKET / VECTORSTORE_S3_PREFIX
    bucket = _env("S3_BUCKET_NAME") or _env("VECTORSTORE_S3_BUCKET")
    prefix = _env("S3_PREFIX") or _env("VECTORSTORE_S3_PREFIX") or "vectorstore/prod"
    return bucket, prefix

def _normalize_model_id(raw: str | None) -> str | None:
    if not raw:
        return None
    # ":0" のようなサフィックスが来たら除去（実装差吸収）
    return raw.split(":")[0]

def build_or_load_vectorstore(docs=None):
    try:
        bucket, prefix = _resolve_bucket_prefix()
        region = _env("AWS_REGION") or "ap-northeast-1"
        model_id = _normalize_model_id(_env("BEDROCK_EMBEDDINGS_MODEL_ID"))

        log.info("=== RAG init start ===")
        log.info("CONFIG bucket=%s prefix=%s model=%s region=%s", bucket, prefix, model_id, region)
        print(f"CONFIG bucket={bucket} prefix={prefix} model={model_id} region={region}")

        if not bucket or not prefix:
            raise RuntimeError("Missing S3 config: S3_BUCKET_NAME / S3_PREFIX")

        local_dir = "/tmp/vectorstore"
        Path(local_dir).mkdir(parents=True, exist_ok=True)

        # S3 → local 同期
        ensure_vectorstore_local(bucket=bucket, prefix=prefix, local_dir=local_dir)
        log.info("S3 download completed to %s", local_dir)

        # Embeddings / FAISS 読み込み
        embeddings = BedrockEmbeddings(model_id=model_id, region_name=region)
        vs = FAISS.load_local(local_dir, embeddings, allow_dangerous_deserialization=True)
        log.info("FAISS loaded successfully from %s", local_dir)
        return vs

    except Exception as e:
        print("=== FAISS init failed ===")
        traceback.print_exc()
        log.exception("FAISS init failed: %s", e)
        raise

def search_vendors(vs, query: str, k: int = 5):
    try:
        results = vs.similarity_search_with_score(query, k=k)
        log.info("search ok: query=%r hits=%d", query, len(results))
        return results
    except Exception:
        log.exception("search failed: query=%r", query)
        raise

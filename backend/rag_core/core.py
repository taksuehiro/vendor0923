# backend/rag_core/core.py
import logging
import os
import traceback
from pathlib import Path
from langchain_community.vectorstores import FAISS
from backend.rag_core.bedrock_embeddings import BedrockEmbeddings
from backend.rag_core_s3 import ensure_vectorstore_local

log = logging.getLogger(__name__)

def _env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)

def _resolve_bucket_prefix():
    # 正: S3_BUCKET_NAME / S3_PREFIX
    # 後方互換: VECTORSTORE_S3_BUCKET / VECTORSTORE_S3_PREFIX
    bucket = _env("S3_BUCKET_NAME") or _env("VECTORSTORE_S3_BUCKET")
    prefix = _env("S3_PREFIX") or _env("VECTORSTORE_S3_PREFIX") or "vectorstore/prod"
    print(f"🔍 DEBUG: _resolve_bucket_prefix() - bucket={bucket}, prefix={prefix}")
    return bucket, prefix

def _normalize_model_id(raw: str | None) -> str | None:
    if not raw:
        return None
    # ":0" のようなサフィックスが来たら除去（実装差吸収）
    return raw.split(":")[0]

def build_or_load_vectorstore(docs=None):
    try:
        print("🔍 DEBUG: Starting build_or_load_vectorstore()")
        bucket, prefix = _resolve_bucket_prefix()
        region = _env("AWS_REGION") or "ap-northeast-1"
        model_id = _normalize_model_id(_env("BEDROCK_EMBEDDINGS_MODEL_ID"))

        print(f"🔍 DEBUG: bucket={bucket}, prefix={prefix}, region={region}, model_id={model_id}")
        log.info("=== RAG init start ===")
        log.info("CONFIG bucket=%s prefix=%s model=%s region=%s", bucket, prefix, model_id, region)
        print(f"CONFIG bucket={bucket} prefix={prefix} model={model_id} region={region}")
        print(f"✅ Normalized model_id: {model_id}")

        if not bucket or not prefix:
            print(f"❌ DEBUG: Missing S3 config - bucket={bucket}, prefix={prefix}")
            raise RuntimeError("Missing S3 config: S3_BUCKET_NAME / S3_PREFIX")

        local_dir = "/tmp/vectorstore"
        Path(local_dir).mkdir(parents=True, exist_ok=True)

        # S3 → local 同期
        print(f"🔍 DEBUG: Starting S3 sync - bucket={bucket}, prefix={prefix}, local_dir={local_dir}")
        ensure_vectorstore_local(bucket=bucket, prefix=prefix, local_dir=local_dir)
        print("🔍 DEBUG: S3 sync completed")
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
        raw_results = vs.similarity_search_with_score(query, k=k)
        # FAISSのL2距離²を類似度スコアに変換
        results = []
        for doc, score in raw_results:
            # 距離²を距離に変換してから類似度に反転
            distance = score ** 0.5  # 距離² → 距離
            similarity = 1 / (1 + distance)  # 距離0→1.0、距離が遠いほど0に近づく
            results.append((doc, similarity))
        
        log.info("search ok: query=%r hits=%d", query, len(results))
        return results
    except Exception:
        log.exception("search failed: query=%r", query)
        raise

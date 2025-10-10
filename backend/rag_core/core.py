import logging
import os
import traceback
from pathlib import Path
import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import BedrockEmbeddings
from backend.rag_core_s3 import ensure_vectorstore_local

log = logging.getLogger(__name__)

def _env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)

def _resolve_bucket_prefix():
    bucket = _env("S3_BUCKET_NAME") or _env("VECTORSTORE_S3_BUCKET")
    prefix = _env("S3_PREFIX") or _env("VECTORSTORE_S3_PREFIX") or "vectorstore/prod"
    log.info(f"🔍 DEBUG: _resolve_bucket_prefix() - bucket={bucket}, prefix={prefix}")
    return bucket, prefix

def _normalize_model_id(raw: str | None) -> str | None:
    if not raw:
        return None
    return raw.split(":")[0]

def build_or_load_vectorstore(docs=None):
    try:
        log.info("🔍 DEBUG: Starting build_or_load_vectorstore()")
        bucket, prefix = _resolve_bucket_prefix()
        region = _env("AWS_REGION") or "ap-northeast-1"
        model_id = _normalize_model_id(_env("BEDROCK_EMBEDDINGS_MODEL_ID"))

        log.info(f"CONFIG bucket={bucket} prefix={prefix} model={model_id} region={region}")

        if not bucket or not prefix:
            raise RuntimeError("Missing S3 config: S3_BUCKET_NAME / S3_PREFIX")

        local_dir = "/tmp/vectorstore"
        Path(local_dir).mkdir(parents=True, exist_ok=True)
        ensure_vectorstore_local(bucket=bucket, prefix=prefix, local_dir=local_dir)
        embeddings = BedrockEmbeddings(model_id=model_id, region_name=region)
        vs = FAISS.load_local(local_dir, embeddings, allow_dangerous_deserialization=True)
        log.info("FAISS loaded successfully from %s", local_dir)
        return vs

    except Exception as e:
        traceback.print_exc()
        log.exception("FAISS init failed: %s", e)
        raise

def search_vendors(vs, query: str, k: int = 5):
    """FAISSベース検索 + 類似度計算（NaN防止＆float32対応）"""
    import math

    try:
        # === DEBUG: embedding 出力確認 ===
        vec = vs.embedding_function(query)
        log.info("🧠 DEBUG Bedrock embedding stats: NaN=%s Sum=%s Min=%s Max=%s Len=%s",
                 np.isnan(vec).any(),
                 float(np.sum(vec)),
                 float(np.min(vec)),
                 float(np.max(vec)),
                 len(vec))

        raw_results = vs.similarity_search_with_score(query, k=k)

        results = []
        for doc, score in raw_results:
            # numpy型対応 & 負値防止
            s = float(score) if score is not None else 0.0
            s = max(s, 0.0)
            distance = math.sqrt(s)
            similarity = float(1.0 / (1.0 + distance))
            if math.isnan(similarity):
                similarity = 0.0
            results.append({
                "page_content": doc.page_content,
                "metadata": doc.metadata,
                "similarity": similarity
            })
        return results

    except Exception:
        log.exception("search failed: query=%r", query)
        raise


if __name__ == "__main__":
    print("🔍 Running BedrockEmbeddings + FAISS test ...")

    from backend.rag_core.core import build_or_load_vectorstore, search_vendors

    vs = build_or_load_vectorstore()
    query = "トヨタ 通商 DX"
    results = search_vendors(vs, query, k=3)

    print("\n=== 検索結果 ===")
    for r in results:
        print(f"- {r['metadata'].get('vendor_id','(no id)')} : similarity={r['similarity']}")

import logging, os
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from typing import List, Optional

log = logging.getLogger(__name__)

S3_BUCKET = os.getenv("S3_BUCKET_NAME") or os.getenv("RAG_S3_BUCKET")
S3_PREFIX = os.getenv("S3_PREFIX") or os.getenv("RAG_S3_PREFIX")
_MODEL_RAW = os.getenv("BEDROCK_EMBEDDINGS_MODEL_ID") or os.getenv("RAG_EMBEDDING") or "amazon.titan-embed-text-v2"
BEDROCK_MODEL_ID = _MODEL_RAW.replace(":0", "")

def _s3_download(bucket: str, key: str, dst: Path):
    """S3からファイルをダウンロード"""
    s3 = boto3.client("s3")
    s3.download_file(bucket, key, str(dst))

def _download_vectorstore_from_s3(local_dir: Path) -> bool:
    log.info("S3 download start: bucket=%s prefix=%s local=%s", S3_BUCKET, S3_PREFIX, local_dir)
    try:
        local_dir.mkdir(parents=True, exist_ok=True)
        for key in ("index.faiss","index.pkl"):
            s3_key = f"{S3_PREFIX.rstrip('/')}/{key}"
            dst = local_dir / key
            _s3_download(S3_BUCKET, s3_key, dst)
            log.info("S3 downloaded: s3://%s/%s -> %s (exists=%s size=%s)",
                     S3_BUCKET, s3_key, dst, dst.exists(), dst.stat().st_size if dst.exists() else -1)
        return True
    except Exception:
        log.exception("S3 download failed")
        return False

def build_or_load_vectorstore(docs=None):
    try:
        local = Path("/tmp/vectorstore")
        has_remote = _download_vectorstore_from_s3(local)
        embeddings = BedrockEmbeddings(model_id=BEDROCK_MODEL_ID)
        if has_remote:
            vs = FAISS.load_local(local, embeddings, allow_dangerous_deserialization=True)
            log.info("FAISS loaded from %s (model=%s)", local, BEDROCK_MODEL_ID)
            return vs
        if docs:
            vs = FAISS.from_documents(docs, embeddings)
            log.info("FAISS built from docs (model=%s)", BEDROCK_MODEL_ID)
            return vs
        raise RuntimeError("No vectorstore available (S3 download failed and no docs)")
    except Exception:
        log.exception("FAISS init failed")
        raise

def search_vendors(vs, query: str, k: int = 5):
    try:
        results = vs.similarity_search_with_score(query, k=k)
        log.info("search ok: query=%r hits=%d", query, len(results))
        return results
    except Exception:
        log.exception("search failed: query=%r", query)
        raise

import logging
import traceback
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import BedrockEmbeddings

log = logging.getLogger(__name__)

def build_or_load_vectorstore(docs=None):
    try:
        log.info("=== RAG init start ===")
        print("=== RAG init start ===")

        # ここでS3_BUCKET_NAMEやS3_PREFIXを確認
        import os
        bucket = os.getenv("S3_BUCKET_NAME")
        prefix = os.getenv("S3_PREFIX")
        model = os.getenv("BEDROCK_EMBEDDINGS_MODEL_ID")
        region = os.getenv("AWS_REGION")
        print(f"CONFIG: bucket={bucket}, prefix={prefix}, model={model}, region={region}")

        local = Path("/tmp/vectorstore")
        local.mkdir(parents=True, exist_ok=True)

        embeddings = BedrockEmbeddings(model_id=model, region_name=region)
        vs = FAISS.load_local(local, embeddings, allow_dangerous_deserialization=True)
        log.info("FAISS loaded successfully")
        print("FAISS loaded successfully")

        return vs
    except Exception as e:
        print("=== FAISS init failed ===")
        traceback.print_exc()
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

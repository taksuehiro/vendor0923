import os
import tempfile
from pathlib import Path
from typing import List, Optional

import boto3
from botocore.exceptions import ClientError

from langchain_aws import BedrockEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-1")
BEDROCK_EMBEDDINGS_MODEL_ID = os.getenv("BEDROCK_EMBEDDINGS_MODEL_ID", "amazon.titan-embed-text-v1")
S3_BUCKET = os.getenv("S3_BUCKET_NAME")
S3_PREFIX = os.getenv("S3_PREFIX", "vectorstores/dev")

def init_embeddings() -> BedrockEmbeddings:
    return BedrockEmbeddings(
        model_id=BEDROCK_EMBEDDINGS_MODEL_ID,
        region_name=AWS_REGION,
    )

def _s3():
    return boto3.client("s3", region_name=AWS_REGION)

def _download_vectorstore_from_s3(local_dir: Path) -> bool:
    if not S3_BUCKET:
        return False
    s3 = _s3()
    keys = [f"{S3_PREFIX}/index.faiss", f"{S3_PREFIX}/index.pkl"]
    ok_any = False
    local_dir.mkdir(parents=True, exist_ok=True)
    for key in keys:
        try:
            local_path = local_dir / Path(key).name
            s3.download_file(S3_BUCKET, key, str(local_path))
            ok_any = True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") != "404":
                raise
    return ok_any

def _upload_vectorstore_to_s3(local_dir: Path):
    if not S3_BUCKET:
        return
    s3 = _s3()
    for name in ("index.faiss", "index.pkl"):
        p = local_dir / name
        if p.exists():
            s3.upload_file(str(p), S3_BUCKET, f"{S3_PREFIX}/{name}")

def build_or_load_vectorstore(docs: Optional[List[Document]] = None) -> FAISS:
    embeddings = init_embeddings()
    with tempfile.TemporaryDirectory() as td:
        local = Path(td)
        has_remote = _download_vectorstore_from_s3(local)

        if has_remote:
            vs = FAISS.load_local(local, embeddings, allow_dangerous_deserialization=True)
            return vs

        if not docs:
            raise RuntimeError("No existing vectorstore in S3 and no docs provided to build one.")

        vs = FAISS.from_documents(docs, embeddings)
        vs.save_local(local)
        _upload_vectorstore_to_s3(local)
        return vs

def search_vendors(vs: FAISS, query: str, k: int = 5):
    results = vs.similarity_search_with_score(query, k=k)
    payload = []
    for doc, score in results:
        payload.append({
            "text": doc.page_content,
            "score": float(score),
            "metadata": doc.metadata or {},
        })
    return payload

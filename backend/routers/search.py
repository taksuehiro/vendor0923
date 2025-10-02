# backend/routers/search.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os, tempfile, shutil, boto3
from botocore.exceptions import ClientError

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import BedrockEmbeddings

router = APIRouter()

# ---- 環境変数（ECS タスク定義 or .env で設定）----
S3_BUCKET  = os.environ.get("RAG_S3_BUCKET", "vendor-rag-0919")
S3_PREFIX  = os.environ.get("RAG_S3_PREFIX", "vectorstores/prod")  # 例
AWS_REGION = os.environ.get("AWS_REGION", "ap-northeast-1")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", AWS_REGION)
EMBED_MODEL_ID = os.environ.get("BEDROCK_EMBED_MODEL", "amazon.titan-embed-text-v2:0")

# ---- グローバルキャッシュ（毎リクエストでS3ダウンロードしない）----
_vectordb = None
_embeddings = None

class SearchRequest(BaseModel):
    query: str
    k: int = 8
    use_mmr: bool = True

def _init_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = BedrockEmbeddings(
            model_id=EMBED_MODEL_ID,
            region_name=BEDROCK_REGION,
        )
    return _embeddings

def _load_faiss_from_s3():
    """
    S3の prefix 配下に保存された LangChain FAISS を /tmp に展開してロードします。
    """
    global _vectordb
    if _vectordb is not None:
        return _vectordb

    s3 = boto3.resource("s3", region_name=AWS_REGION)
    bucket = s3.Bucket(S3_BUCKET)

    # 一時ディレクトリへ同期
    tmpdir = tempfile.mkdtemp(prefix="faiss_")
    local_dir = os.path.join(tmpdir, "faiss")
    os.makedirs(local_dir, exist_ok=True)

    try:
        # S3 -> /tmp にプレーンコピー
        prefix = S3_PREFIX.rstrip("/") + "/"
        for obj in bucket.objects.filter(Prefix=prefix):
            rel = obj.key[len(prefix):]
            if rel == "" or rel.endswith("/"):
                continue
            dst_path = os.path.join(local_dir, rel)
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            bucket.download_file(obj.key, dst_path)
    except ClientError as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"S3 download error: {e}")

    try:
        _vectordb = FAISS.load_local(
            folder_path=local_dir,
            embeddings=_init_embeddings(),
            allow_dangerous_deserialization=True,  # LangChain 0.1+ で必要
        )
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"FAISS load error: {e}")

    # tmpdir はプロセス存続中は保持（ECSタスク再起動で再ロード）
    return _vectordb

@router.post("/search")
async def search(req: SearchRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query is empty")

    vectordb = _load_faiss_from_s3()
    retriever = vectordb.as_retriever(
        search_kwargs={"k": req.k, "maximal_marginal_relevance": req.use_mmr}
    )

    try:
        docs = retriever.get_relevant_documents(req.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"retrieve error: {e}")

    # 結果をフロントのUIに合わせて返す
    hits = []
    for i, d in enumerate(docs):
        meta = d.metadata or {}
        hits.append({
            "id": meta.get("id") or f"doc-{i+1}",
            "title": meta.get("title") or meta.get("source") or f"Document {i+1}",
            "snippet": d.page_content[:600],
            "score": meta.get("score"),   # あれば
            "url": meta.get("url") or meta.get("source"),
            "metadata": meta,
        })
    return {"status": "ok", "hits": hits}

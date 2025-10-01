from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain.docstore.document import Document

from backend.models import SearchRequest, SearchResponse, SearchHit
from backend.rag_core import build_or_load_vectorstore, search_vendors

app = FastAPI(title="Vendor RAG API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: 本番は制限推奨
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_VECTORSTORE = None

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    global _VECTORSTORE
    if _VECTORSTORE is None:
        try:
            _VECTORSTORE = build_or_load_vectorstore()
        except Exception as e:
            # 初回に S3 が空だった場合だけ、最小シードで作成（今回は S3 を先置き済みなので通常は通らない）
            seed_docs = [
                Document(page_content="Vendor A provides Bedrock integration for embeddings.", metadata={"vendor":"A"}),
                Document(page_content="Vendor B supports S3 archival of logs.", metadata={"vendor":"B"}),
                Document(page_content="Titan embeddings via Amazon Bedrock return 1536-d vectors.", metadata={"note":"titan"})
            ]
            try:
                _VECTORSTORE = build_or_load_vectorstore(seed_docs)
            except Exception as inner:
                raise HTTPException(status_code=500, detail=str(inner)) from inner

    try:
        hits = search_vendors(_VECTORSTORE, req.query, k=req.k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return SearchResponse(results=[SearchHit(**h) for h in hits])
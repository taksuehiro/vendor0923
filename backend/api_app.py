from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

from rag_core.rag_core import get_rag, search_vendors  # local固定

app = FastAPI()
log = logging.getLogger("uvicorn")

# CORS: 開発中はワイルドカード、credentialsはFalseで整合
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchBody(BaseModel):
    query: str
    k: int | None = 5
    use_mmr: bool | None = False

@app.get("/health", include_in_schema=False)
def health():
    return {"status": "ok"}  # 依存不要

@app.get("/search")
def search_get(query: str = Query(...), k: int = 5, use_mmr: bool = False):
    if not query:
        raise HTTPException(status_code=422, detail="empty query")
    try:
        results = search_vendors(query, top_k=k)
        return {"query": query, "hits": results}
    except Exception as e:
        log.error(f"Search failed: {e}")
        return {"query": query, "hits": [], "error": str(e)}

@app.post("/search")
def search_post(body: SearchBody):
    if not body.query:
        raise HTTPException(status_code=422, detail="empty query")
    try:
        results = search_vendors(body.query, top_k=body.k or 5)
        return {"query": body.query, "hits": results}
    except Exception as e:
        log.error(f"Search failed: {e}")
        return {"query": body.query, "hits": [], "error": str(e)}

@app.post("/auth/verify")
def verify(payload: dict):
    if payload.get("email") == "demo@example.com" and payload.get("password") == "secret":
        return {"id": 1, "email": payload["email"], "org_id": 1}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.on_event("startup")
def _warm_vectorstore():
    try:
        get_rag()  # localのFAISSをロード
        log.info(f"[startup] vectorstore source: local")
    except Exception as e:
        log.warning(f"[warmup] vectorstore init failed (local): {e}")

@app.get("/__version")
def version():
    try:
        with open("/app/BUILD_INFO","r") as f:
            return {"ok": True, "build": f.read().strip()}
    except Exception:
        return {"ok": True, "build": "unknown"}
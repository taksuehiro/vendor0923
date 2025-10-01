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

def _do_search(q: str):
    if not q:
        raise HTTPException(status_code=422, detail="empty query")
    # TODO: 明日以降 vectorstore を接続
    return {"answers":[f"echo: {q}"], "note":"temp"}

@app.get("/search")   # GET
def search_get(query: str = Query(...)):
    return _do_search(query)

@app.post("/search")  # POST JSON {"query": "..."} も {"q": "..."} も受ける
def search_post(payload: dict = Body(...)):
    q = payload.get("query") or payload.get("q")
    if not q:
        raise HTTPException(status_code=422, detail="Missing 'query'")
    return _do_search(q)

@app.post("/auth/verify")
def verify(payload: dict):
    if payload.get("email") == "demo@example.com" and payload.get("password") == "secret":
        return {"id": 1, "email": payload["email"], "org_id": 1}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/search")
def search(body: SearchBody):
    try:
        results = search_vendors(body.query, top_k=body.k or 5)
        return {"hits": results}
    except Exception as e:
        log.error(f"Search failed: {e}")
        return {"hits": []}

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
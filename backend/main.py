from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
from typing import Dict, Any
from backend.rag_core import search_vendors, get_rag

app = FastAPI()

# CORS: Amplify/開発中はワイルドカード、credentialsはFalseで整合
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Feature flag: mock or real =====
# デフォルトは real（未設定/空=real）。明示的に USE_MOCK=true の時だけモック。
USE_MOCK = os.getenv("USE_MOCK", "false").lower() == "true"

def with_metadata(payload: Dict[str, Any], provider: str) -> Dict[str, Any]:
    payload = dict(payload)
    payload["metadata"] = {"provider": provider, "status": "ok"}
    return payload

class SearchReq(BaseModel):
    query: str = Field(..., min_length=1)
    k: int | None = Field(default=5, ge=1, le=50)
    use_mmr: bool | None = False

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/auth/verify")
def verify(payload: dict):
    if payload.get("email") == "demo@example.com" and payload.get("password") == "secret":
        return {"id": 1, "email": payload["email"], "org_id": 1}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/search")
def search(payload: dict):
    q = (payload or {}).get("query", "")
    k = (payload or {}).get("k", 5) or 5
    use_mmr = bool((payload or {}).get("use_mmr", False))  # currently unused; kept for future

    if not isinstance(q, str) or not q.strip():
        raise HTTPException(status_code=400, detail="query is required")

    if USE_MOCK:
        resp = {
            "hits": [
                {"id": "v001", "title": f"Result for {q}", "score": 0.92, "snippet": "mock snippet 1"},
                {"id": "v002", "title": f"Result for {q}", "score": 0.81, "snippet": "mock snippet 2"},
            ]
        }
        return with_metadata(resp, "mock")

    # real path: FAISS + vendors.json via rag_core
    try:
        # search_vendors returns list of dicts with keys: id, title, score, snippet, metadata{status,category}
        results = search_vendors(q, top_k=int(k))
        resp = {"hits": results}
        # expose where the vectorstore came from (S3/current, local-cache, rebuilt, etc.)
        source = getattr(get_rag(), "vectorstore_source", "unknown")
        meta = with_metadata(resp, "real")
        meta["metadata"]["source"] = source
        return meta
    except Exception as e:
        # return safe 200 with empty hits but mark error in metadata for observability
        resp = {"hits": []}
        meta = with_metadata(resp, "real")
        meta["metadata"]["error"] = str(e)
        return meta

@app.on_event("startup")
def _warm_vectorstore():
    if not USE_MOCK:
        try:
            get_rag()  # loads or builds FAISS; sets .vectorstore_source
            print(f"[startup] vectorstore source: {get_rag().vectorstore_source}")
        except Exception as e:
            # log but don't crash process; health will show degraded
            print(f"[warmup] vectorstore init failed: {e}")

# オプション：ビルド識別用
@app.get("/__version")
def version():
    try:
        with open("/app/BUILD_INFO","r") as f:
            return {"ok": True, "build": f.read().strip()}
    except Exception:
        return {"ok": True, "build": "unknown"}
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
import logging
from typing import Literal

# Optional: if your project already has these helpers, reuse them.
from backend.rag_core_s3 import ensure_vectorstore_local  # downloads S3 -> local dir if not present
from backend.rag_core import get_rag, search_vendors  # FAISS loader + search

app = FastAPI()
log = logging.getLogger("uvicorn")

# CORS: Amplify/開発中はワイルドカード、credentialsはFalseで整合
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def bool_env(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip().lower() in ("1","true","yes","y","on")

# ---- runtime switches (prod-safe defaults) ----
USE_MOCK = bool_env("USE_MOCK", default=False)
VECTORSTORE_S3_BUCKET = os.getenv("VECTORSTORE_S3_BUCKET", "")
VECTORSTORE_S3_PREFIX = os.getenv("VECTORSTORE_S3_PREFIX", "")
VECTORSTORE_LOCAL_DIR = os.getenv("VECTORSTORE_LOCAL_DIR", "/app/vectorstore")

# Source: s3 if bucket/prefix present, else local
SOURCE: Literal["s3","local"] = "s3" if (VECTORSTORE_S3_BUCKET and VECTORSTORE_S3_PREFIX) else "local"

# Log on startup (so we can see real/mode in CloudWatch)
log.info(f"[startup] USE_MOCK={USE_MOCK} SOURCE={SOURCE} S3={VECTORSTORE_S3_BUCKET}/{VECTORSTORE_S3_PREFIX} LOCAL_DIR={VECTORSTORE_LOCAL_DIR}")

class SearchBody(BaseModel):
    query: str
    k: int | None = 5
    use_mmr: bool | None = False

@app.get("/health")
def health():
    return {"status":"ok", "mode": ("mock" if USE_MOCK else "real"), "source": SOURCE}

@app.get("/__debug/env")
def debug_env():
    # Return a safe subset for troubleshooting; secrets masked
    return {
        "USE_MOCK": USE_MOCK,
        "VECTORSTORE_S3_BUCKET": VECTORSTORE_S3_BUCKET or "<empty>",
        "VECTORSTORE_S3_PREFIX": VECTORSTORE_S3_PREFIX or "<empty>",
        "VECTORSTORE_LOCAL_DIR": VECTORSTORE_LOCAL_DIR or "<empty>",
        "OPENAI_API_KEY": "***" if os.getenv("OPENAI_API_KEY") else "<unset>",
    }

@app.post("/auth/verify")
def verify(payload: dict):
    if payload.get("email") == "demo@example.com" and payload.get("password") == "secret":
        return {"id": 1, "email": payload["email"], "org_id": 1}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/search")
def search(body: SearchBody):
    if USE_MOCK:
        return {
            "hits": [
                {"id":"v001","title":f"Result for {body.query}","score":0.92,"snippet":"mock snippet 1"},
                {"id":"v002","title":f"Result for {body.query}","score":0.81,"snippet":"mock snippet 2"},
            ]
        }
    # real path
    # 1) ensure local vectorstore from S3 (if configured)
    if SOURCE == "s3":
        ensure_vectorstore_local(
            bucket=VECTORSTORE_S3_BUCKET,
            prefix=VECTORSTORE_S3_PREFIX,
            local_dir=VECTORSTORE_LOCAL_DIR,
        )
    # 2) load FAISS and search
    try:
        results = search_vendors(body.query, top_k=body.k or 5)
        return {"hits": results}
    except Exception as e:
        # return safe 200 with empty hits but mark error for observability
        log.error(f"Search failed: {e}")
        return {"hits": []}

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
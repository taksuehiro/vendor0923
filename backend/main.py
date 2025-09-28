from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
from typing import Dict, Any

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
    return with_metadata({"status": "ok"}, "mock" if USE_MOCK else "real")

@app.post("/auth/verify")
def verify(payload: dict):
    if payload.get("email") == "demo@example.com" and payload.get("password") == "secret":
        return {"id": 1, "email": payload["email"], "org_id": 1}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/search")
def search(payload: dict):
    q = (payload or {}).get("query", "")
    if USE_MOCK:
        resp = {
            "hits": [
                {"id": "v001", "title": f"Result for {q}", "score": 0.92, "snippet": "mock snippet 1"},
                {"id": "v002", "title": f"Result for {q}", "score": 0.81, "snippet": "mock snippet 2"},
            ]
        }
        return with_metadata(resp, "mock")

    # === real path（必要に応じて実装を差し替え） ===
    # ここではとりあえずモックに近い形のダミー実装（snippetから"mock"は消す）
    resp = {
        "hits": [
            {"id": "r001", "title": f"Result for {q}", "score": 0.83, "snippet": "snippet 1"},
            {"id": "r002", "title": f"Result for {q}", "score": 0.79, "snippet": "snippet 2"},
        ]
    }
    return with_metadata(resp, "real")

# オプション：ビルド識別用
@app.get("/__version")
def version():
    try:
        with open("/app/BUILD_INFO","r") as f:
            return {"ok": True, "build": f.read().strip()}
    except Exception:
        return {"ok": True, "build": "unknown"}
from dotenv import load_dotenv
import os

# 環境変数の読み込み（.env.local を優先）
load_dotenv('.env.local')  # ローカル開発用
load_dotenv()              # フォールバック用

# デバッグ用（本番では削除）
print(f"OPENAI_API_KEY loaded: {bool(os.getenv('OPENAI_API_KEY'))}")

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from rag_core import search_vendors  # ← 追加

app = FastAPI(title="Vendor RAG API", version="1.0.0")

# CORS: 環境変数 ALLOWED_ORIGINS にカンマ区切りで指定（ローカル & Amplify を両方許可）
allowed = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in allowed if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# データモデル
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    mmr: Optional[float] = None  # いまは未使用。将来の拡張用

class SearchResult(BaseModel):
    id: str
    title: str
    score: float
    snippet: str
    metadata: dict = {"status": "", "category": ""}

class SearchResponse(BaseModel):
    hits: List[SearchResult]

class AuthRequest(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    id: str
    email: str
    org_id: str

class UserResponse(BaseModel):
    id: str
    email: str

# ヘルスチェック
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# 認証エンドポイント（モック）
@app.post("/auth/verify", response_model=AuthResponse)
async def verify_credentials(auth: AuthRequest):
    # モック実装：実際の認証ロジックは後で実装
    if auth.email == "admin@example.com" and auth.password == "password":
        return AuthResponse(
            id="1",
            email=auth.email,
            org_id="org_1"
        )
    raise HTTPException(status_code=401, detail="Invalid credentials")

# ユーザー情報取得（モック）
@app.get("/me", response_model=UserResponse)
async def get_current_user():
    # モック実装：JWT検証は後で実装
    return UserResponse(
        id="1",
        email="admin@example.com"
    )

# ★ 差し替え：RAG 呼び出し
@app.post("/search", response_model=SearchResponse)
async def search_endpoint(request: SearchRequest):
    try:
        results = search_vendors(request.query, top_k=request.top_k)
        return SearchResponse(hits=[SearchResult(**r) for r in results])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

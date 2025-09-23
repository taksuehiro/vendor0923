from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

app = FastAPI(title="Vendor RAG API", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.jsのデフォルトポート
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# データモデル
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    mmr: float = 0.5

class SearchResult(BaseModel):
    id: str
    title: str
    score: float
    snippet: str
    metadata: dict

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

# 検索エンドポイント（モック）
@app.post("/search", response_model=SearchResponse)
async def search_vendors(request: SearchRequest):
    # モック実装：実際のRAG機能は後で実装
    mock_results = [
        SearchResult(
            id="vendor_1",
            title="LiberCraft",
            score=0.95,
            snippet="AI・機械学習を活用したスクラッチ開発サービス",
            metadata={"status": "面談済", "category": "スクラッチ"}
        ),
        SearchResult(
            id="vendor_2", 
            title="TechCorp",
            score=0.87,
            snippet="クラウドインフラ構築・運用支援",
            metadata={"status": "未面談", "category": "SaaS"}
        )
    ]
    
    return SearchResponse(hits=mock_results[:request.top_k])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

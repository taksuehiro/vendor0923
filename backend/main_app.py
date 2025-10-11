# backend/main_app.py
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers.search import router as search_router
from backend.rag_core.core import build_or_load_vectorstore  # ← 余計な定数importを削除

log = logging.getLogger(__name__)
app = FastAPI()

# CORSミドルウェアは起動イベントより前に追加する
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://main.d167z8rnntj0xs.amplifyapp.com",  # Amplify URL
        "http://localhost:3000",  # ローカル開発用
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # 起動時に設定を明示
    log.info(
        "CONFIG(startup) bucket=%s prefix=%s model=%s region=%s",
        os.getenv("S3_BUCKET_NAME") or os.getenv("VECTORSTORE_S3_BUCKET"),
        os.getenv("S3_PREFIX") or os.getenv("VECTORSTORE_S3_PREFIX"),
        os.getenv("BEDROCK_EMBEDDINGS_MODEL_ID"),
        os.getenv("AWS_REGION"),
    )
    try:
        build_or_load_vectorstore()
        log.info("✅ FAISS vectorstore loaded successfully")
    except Exception as e:
        log.error("❌ Failed to load FAISS vectorstore: %s", e)
        # ここでraiseしておくと致命時は起動させない判断も可
        # raise e

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(search_router)
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.search import router as search_router
from rag_core.core import build_or_load_vectorstore, S3_BUCKET, S3_PREFIX, BEDROCK_MODEL_ID

log = logging.getLogger(__name__)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """アプリ起動時にS3からFAISSインデックスをロード"""
    # 設定確認ログを追加
    log.info("CONFIG: bucket=%s prefix=%s model=%s region=%s",
             S3_BUCKET, S3_PREFIX, BEDROCK_MODEL_ID, os.getenv("AWS_REGION"))
    
    try:
        build_or_load_vectorstore()
        log.info("✅ FAISS vectorstore loaded successfully")
    except Exception as e:
        log.error(f"❌ Failed to load FAISS vectorstore: {e}")
        raise e

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://main.d167z8rnntj0xs.amplifyapp.com",  # あなたのAmplify URL
        # 独自ドメインを使う場合はここに追加
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(search_router)
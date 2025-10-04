from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.search import router as search_router
from vectorstore import load_vectorstore

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """アプリ起動時にS3からFAISSインデックスをロード"""
    try:
        load_vectorstore()
        print("✅ FAISS vectorstore loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load FAISS vectorstore: {e}")
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
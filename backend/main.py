from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI()

# CORS: Amplify/開発中はワイルドカード、credentialsはFalseで整合
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
def search(req: SearchReq):
    q = req.query
    return {"hits": [
        {
            "id": "v001", 
            "title": f"Result for {q}", 
            "score": 0.92, 
            "snippet": "mock snippet 1",
            "metadata": {
                "status": "面談済",
                "category": "スクラッチ"
            }
        },
        {
            "id": "v002", 
            "title": f"Result for {q}", 
            "score": 0.81, 
            "snippet": "mock snippet 2",
            "metadata": {
                "status": "未面談",
                "category": "SaaS"
            }
        },
    ]}

# オプション：ビルド識別用
@app.get("/__version")
def version():
    try:
        with open("/app/BUILD_INFO","r") as f:
            return {"ok": True, "build": f.read().strip()}
    except Exception:
        return {"ok": True, "build": "unknown"}
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# Amplify の URL を直接指定
origins = [
    "https://main.dcs5uerijxlhh.amplifyapp.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # "*" は避ける
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    q = payload.get("query", "")
    return {"hits": [
        {"id": "v001", "title": f"Result for {q}", "score": 0.92, "snippet": "mock snippet 1"},
        {"id": "v002", "title": f"Result for {q}", "score": 0.81, "snippet": "mock snippet 2"},
    ]}
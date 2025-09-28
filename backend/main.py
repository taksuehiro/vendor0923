import uuid
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from models import SearchReq, SearchRes, Hit

log = logging.getLogger("uvicorn.error")

app = FastAPI()

# CORS設定 - まずは全オリジンを許可して動作確認
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では Amplify ドメインに絞るのが望ましい
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_trace_and_log(request: Request, call_next):
    trace_id = request.headers.get("x-trace-id", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    body = await request.body()
    log.info(f"[REQ] {trace_id} {request.method} {request.url.path} "
             f"hdrs={{origin:{request.headers.get('origin')}, content-type:{request.headers.get('content-type')}}} "
             f"body={body[:2048]!r}")
    try:
        resp = await call_next(request)
    finally:
        pass
    resp.headers["x-trace-id"] = trace_id
    log.info(f"[RES] {trace_id} status={resp.status_code}")
    return resp

@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", "-")
    log.exception(f"[ERR] {trace_id} unhandled")
    return JSONResponse(
        status_code=500,
        content={"ok": False, "error": "internal_error", "trace_id": trace_id},
    )

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/auth/verify")
def verify(payload: dict):
    if payload.get("email") == "demo@example.com" and payload.get("password") == "secret":
        return {"id": 1, "email": payload["email"], "org_id": 1}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/search", response_model=SearchRes)
def search(req: SearchReq, request: Request):
    if req.query == "__ERROR_TEST__":
        # 正しく 400 を返す（200にエラーを埋め込まない）
        raise HTTPException(status_code=400, detail="bad_query")
    return SearchRes(
        ok=True,
        hits=[
            Hit(id="v001", title=f"Result for {req.query}", score=0.92, snippet="mock snippet 1"),
            Hit(id="v002", title=f"Result for {req.query}", score=0.81, snippet="mock snippet 2"),
        ],
    )

# 契約のズレ可視化用：そのまま返すエコー
@app.post("/debug/echo")
async def echo(request: Request):
    body = await request.json()
    headers = {k: request.headers.get(k) for k in ["origin", "content-type", "x-trace-id"]}
    return {"method": request.method, "path": request.url.path, "headers": headers, "body": body}
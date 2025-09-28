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
             f"origin={request.headers.get('origin')} ct={request.headers.get('content-type')} "
             f"body={body[:1024]!r}")
    try:
        resp = await call_next(request)
    except Exception:
        log.exception(f"[ERR] {trace_id} unhandled")
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": "internal_error", "trace_id": trace_id},
        )
    resp.headers["x-trace-id"] = trace_id
    log.info(f"[RES] {trace_id} status={resp.status_code}")
    return resp

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/search", response_model=SearchRes)
def search(req: SearchReq):
    return SearchRes(
        ok=True,
        hits=[
            Hit(id="v001", title=f"Result for {req.query}", score=0.92, snippet="mock snippet 1"),
            Hit(id="v002", title=f"Result for {req.query}", score=0.81, snippet="mock snippet 2"),
        ],
    )

@app.post("/debug/echo")
async def echo(request: Request):
    headers = {k: request.headers.get(k) for k in ["origin", "content-type", "x-trace-id"]}
    body = await request.json()
    return {"method": request.method, "path": str(request.url.path), "headers": headers, "body": body}
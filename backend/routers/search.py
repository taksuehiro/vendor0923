from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging
import sys
import traceback
from backend.models import SearchRequest
from backend.rag_core.core import build_or_load_vectorstore, search_vendors

log = logging.getLogger(__name__)

# --- 追加ここから ---
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
handler.setFormatter(formatter)
if not log.handlers:
    log.addHandler(handler)
log.setLevel(logging.INFO)
# --- 追加ここまで ---
router = APIRouter()

# Global vectorstore instance
_vs = None

def do_search(query: str, k: int = 5):
    """Search function that uses the global vectorstore"""
    global _vs
    if _vs is None:
        _vs = build_or_load_vectorstore()
    return search_vendors(_vs, query, k)

def normalize(results):
    """Normalize search results to expected format"""
    normalized = []
    for doc, score in results:
        normalized.append({
            "text": doc.page_content,
            "score": float(score),
            "metadata": doc.metadata or {}
        })
    return normalized

@router.post("/search")
async def search(payload: SearchRequest):
    try:
        results = do_search(payload.query, k=payload.k or 5)
        return {"results": normalize(results)}
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        log.error(f"search endpoint failed: {e}\n{tb}")
        return JSONResponse(status_code=500, content={"detail": str(e)})
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import logging
import os
import sys
import traceback
from backend.models import SearchRequest
from backend.rag_core.core import build_or_load_vectorstore, search_vendors
from backend.structured_search import (
    classify_query,
    structured_search,
    hybrid_search
)

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
    """Normalize search results to frontend expected format
    
    Converts:
        page_content -> text
        similarity -> score
        metadata -> metadata
    """
    normalized = []
    for r in results:
        normalized.append({
            "text": r.get("page_content", ""),
            "score": r.get("similarity", 0.0),
            "metadata": r.get("metadata", {})
        })
    return normalized

@router.post("/search")
async def search(payload: SearchRequest):
    try:
        query = payload.query
        k = payload.k or 5
        
        # LLMベースの分類を使用するかどうか（環境変数で制御）
        use_llm_classification = os.getenv("USE_LLM_CLASSIFICATION", "false").lower() == "true"
        
        # クエリを分類
        search_type, filters, semantic_query = classify_query(query, use_llm=use_llm_classification)
        log.info(f"Query: '{query}' → Type: {search_type}, Filters: {filters}, Semantic: '{semantic_query}' (LLM: {use_llm_classification})")
        
        # 検索タイプに応じて処理を分岐
        if search_type == "structured":
            # 純粋な構造化検索（「面談済みの会社」など）
            results = structured_search(filters, k=k)
        
        elif search_type == "hybrid":
            # ハイブリッド検索（「面談済みのチャットボット企業」など）
            results = hybrid_search(filters, semantic_query, k=k)
        
        else:
            # 純粋なセマンティック検索（既存ロジック）
            results = do_search(query, k=k)
        
        # フロントエンドが期待する形式に変換
        normalized_results = normalize(results)
        return {"results": normalized_results}
    
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        log.error(f"search endpoint failed: {e}\n{tb}")
        return JSONResponse(status_code=500, content={"detail": str(e)})
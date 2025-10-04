# backend/routers/search.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from vectorstore import VSTORE

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    k: int = 8
    use_mmr: bool = True

@router.post("/search")
async def search(req: SearchRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query is empty")
    
    if VSTORE is None:
        raise HTTPException(status_code=500, detail="Vector store not loaded")
    
    try:
        if req.use_mmr:
            # MMR検索
            docs_with_scores = VSTORE.max_marginal_relevance_search_with_score(
                query=req.query,
                k=req.k
            )
        else:
            # 類似度検索
            docs_with_scores = VSTORE.similarity_search_with_score(
                query=req.query,
                k=req.k
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {e}")
    
    # 結果を指示に従った形式で返す
    results = []
    for doc, distance in docs_with_scores:
        # 距離を類似度（0〜1）に変換
        score = 1.0 / (1.0 + distance)
        
        results.append({
            "text": doc.page_content,
            "metadata": doc.metadata or {},
            "score": score
        })
    
    return {"results": results}
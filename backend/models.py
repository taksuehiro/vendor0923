from pydantic import BaseModel
from typing import List, Optional

class SearchRequest(BaseModel):
    query: str
    k: int = 5

class SearchHit(BaseModel):
    text: str
    score: Optional[float] = None
    metadata: Optional[dict] = None

class SearchResponse(BaseModel):
    results: List[SearchHit]
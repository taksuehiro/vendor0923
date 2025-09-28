from pydantic import BaseModel, Field

class SearchReq(BaseModel):
    query: str = Field(..., min_length=1)
    k: int = 1
    use_mmr: bool = False

class Hit(BaseModel):
    id: str
    title: str
    score: float
    snippet: str

class SearchRes(BaseModel):
    ok: bool = True
    hits: list[Hit]

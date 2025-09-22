# rag_core/data_models.py
from typing import List, Optional
from pydantic import BaseModel, AnyUrl, Field

class Vendor(BaseModel):
    vendor_id: str = Field(..., description="例: 面談-01")
    name: str
    alias: List[str] = []
    status: str                   # 面談済 / 未面談
    category: str                 # 契約書管理 / AI-OCR ...
    industry_tags: List[str] = [] # ["法務", "全業種"] など
    tech_stack: List[str] = []    # ["AI", "クラウド"] など
    price_range: str              # 低/中/高/要見積
    deployment: str               # SaaS/オンプレ/ハイブリッド
    strength: Optional[str] = None
    overview: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
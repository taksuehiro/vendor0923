# rag_core/loaders/json_loader.py
import json
from pathlib import Path
from typing import List, Union
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from rag_core.data_models import Vendor

def _normalize_vendor(item: dict) -> dict:
    """vendors.jsonの構造をPydanticモデルに合わせて正規化"""
    normalized = {
        "vendor_id": item.get("vendor_id", ""),
        "name": item.get("name", ""),
        "alias": item.get("alias", []),
        "status": item.get("engagement", {}).get("status", "不明"),
        "category": item.get("type", "不明"),
        "industry_tags": item.get("capabilities", []),
        "tech_stack": item.get("capabilities", []),
        "price_range": _extract_price_range(item),
        "deployment": item.get("delivery", {}).get("deployment", "不明"),
        "strength": item.get("notes", ""),
        "overview": item.get("offerings", {}).get("description_short", ""),
        "description": item.get("notes", ""),
        "url": item.get("website", ""),
    }
    return normalized

def _extract_price_range(item: dict) -> str:
    """価格帯を抽出・正規化"""
    man_month = item.get("commercials", {}).get("man_month_jpy", "")
    if not man_month:
        return "要見積"
    
    # 数値範囲の解析
    if "-" in man_month:
        try:
            low, high = man_month.split("-")
            low_val = int(low.strip())
            if low_val < 100:
                return "低"
            elif low_val < 200:
                return "中"
            else:
                return "高"
        except:
            return "要見積"
    else:
        try:
            val = int(man_month.strip())
            if val < 100:
                return "低"
            elif val < 200:
                return "中"
            else:
                return "高"
        except:
            return "要見積"

def _to_content(v: Vendor) -> str:
    lines = [
        f"ベンダー名: {v.name}",
        f"ベンダーID: {v.vendor_id}",
        f"別名: {', '.join(v.alias) if v.alias else '-'}",
        f"カテゴリ: {v.category}",
        f"業界タグ: {', '.join(v.industry_tags) if v.industry_tags else '-'}",
        f"技術スタック: {', '.join(v.tech_stack) if v.tech_stack else '-'}",
        f"価格帯: {v.price_range}",
        f"デプロイ: {v.deployment}",
        f"強み: {v.strength or '-'}",
        f"サービス概要: {v.overview or '-'}",
        f"詳細説明: {v.description or '-'}",
        f"URL: {v.url or '-'}",
    ]
    return "\n".join(lines).strip()

def load_json_as_documents(
    src: Union[str, Path],
    chunk_size: int = 0,
    chunk_overlap: int = 0
) -> List[Document]:
    # ファイルパス or JSON文字列の両対応
    if isinstance(src, (str, Path)) and Path(str(src)).exists():
        raw = Path(src).read_text(encoding="utf-8")
    else:
        raw = str(src)

    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("JSON root must be an array of vendor objects.")

    docs: List[Document] = []
    for i, item in enumerate(data):
        # vendors.jsonの構造を正規化
        normalized_item = _normalize_vendor(item)
        v = Vendor(**normalized_item)
        content = _to_content(v)
        metadata = {
            "vendor_id": v.vendor_id,
            "name": v.name,
            "alias": v.alias,
            "status": v.status,
            "category": v.category,
            "industry_tags": v.industry_tags,
            "tech_stack": v.tech_stack,
            "price_range": v.price_range,
            "deployment": v.deployment,
            "url": str(v.url) if v.url else None,
            "source_format": "json",
            "source_index": i,
            
            # ブラウズUI向けの追加メタ
            "type": item.get("type"),  # SaaS / スクラッチ / SI など
            "listed": (item.get("corporate") or {}).get("listed"),  # "上場" / "未上場" / "不明"
            "investors": (item.get("corporate") or {}).get("investors", []),  # ["投資家A", ...]
            "employees_band": (item.get("corporate") or {}).get("employees_band"),  # "1-10" 等
            "is_scratch": (item.get("delivery") or {}).get("is_scratch"),  # True/False/None
            "use_cases": (item.get("tags") or {}).get("use_cases", []),
            "industries": (item.get("tags") or {}).get("industries", []),
            "departments": (item.get("tags") or {}).get("departments", []),
        }
        if chunk_size and len(content) > chunk_size:
            ts = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=max(0, chunk_overlap)
            )
            for piece in ts.split_text(content):
                if piece.strip():
                    docs.append(Document(page_content=piece.strip(), metadata=metadata))
        else:
            docs.append(Document(page_content=content, metadata=metadata))
    return docs
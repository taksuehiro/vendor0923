# rag_core/loaders/json_loader.py

import json
from langchain.schema import Document

def load_json_as_documents(path: str, chunk_size: int = None, chunk_overlap: int = None):
    """vendors.json (list形式) を読み込んで Document のリストに変換する"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # vendors.json のトップレベルは list
    if isinstance(data, list):
        vendors = data
    elif isinstance(data, dict):
        # 念のため dict に vendors キーがある場合も対応
        vendors = data.get("vendors", [])
    else:
        vendors = []

    docs = []
    for vendor in vendors:
        # 検索対象のテキスト
        content = f"{vendor.get('vendor_id', '')} {vendor.get('name', '')} {vendor.get('type', '')} {vendor.get('notes', '')}"
        # metadata として vendor 全体を保持
        docs.append(Document(page_content=content, metadata=vendor))

    return docs

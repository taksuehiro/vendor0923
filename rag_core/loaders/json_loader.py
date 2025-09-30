# rag_core/loaders/json_loader.py

import json
from langchain.schema import Document

def load_json_as_documents(path: str, chunk_size: int = None, chunk_overlap: int = None):
    """vendors.json を読み込んで Document のリストに変換する"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    docs = []
    for vendor in data.get("vendors", []):
        # page_content に検索対象テキストを入れる
        content = f"{vendor.get('id', '')} {vendor.get('name', '')} {vendor.get('category', '')}"
        # metadata に元のフィールドをそのまま持たせる
        docs.append(Document(page_content=content, metadata=vendor))
    return docs

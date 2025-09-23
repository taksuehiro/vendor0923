# backend/rag_core.py
from __future__ import annotations
import os
import json
from pathlib import Path
from typing import List, Dict, Any

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_core.documents import Document

# 環境変数
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VECTOR_DIR = Path(os.getenv("VECTOR_DIR", "/app/vectorstore")).resolve()
DATA_PATH = Path(os.getenv("VENDOR_DATA_JSON", "/app/data/vendors.json")).resolve()

INDEX_NAME = "vendors"

class VendorRAG:
    def __init__(self) -> None:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY が未設定です。ローカルでは .env.local / .env を、ECS では Secrets Manager 経由で設定してください。")

        self.embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        self.vs: FAISS | None = None

    # 永続パス
    def _index_dir(self) -> Path:
        return VECTOR_DIR / INDEX_NAME

    def _exists(self) -> bool:
        p = self._index_dir()
        return (p / "index.faiss").exists() and (p / "index.pkl").exists()

    def load_or_build(self) -> None:
        VECTOR_DIR.mkdir(parents=True, exist_ok=True)
        if self._exists():
            self.vs = FAISS.load_local(
                str(self._index_dir()),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
            return

        # データ読み込み（最低限のスキーマ: id, name, description, status, category）
        docs: List[Document] = []
        if DATA_PATH.exists():
            items = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        else:
            # フォールバックのサンプル
            items = [
                {"id": "V-LiberCraft", "name": "LiberCraft", "description": "AI・機械学習を活用したスクラッチ開発サービス。契約書管理や法務業務の自動化に強み。", "status": "面談済", "category": "スクラッチ"},
                {"id": "V-TechCorp", "name": "TechCorp", "description": "クラウドインフラ構築・運用支援のSaaS。契約管理ワークフロー連携に実績。", "status": "未面談", "category": "SaaS"},
            ]

        for it in items:
            text = f"{it.get('name','')}。{it.get('description','')}"
            meta = {k: v for k, v in it.items() if k not in ("description",)}
            docs.append(Document(page_content=text, metadata=meta))

        # ベクトルストア作成
        self.vs = FAISS.from_documents(docs, self.embeddings, docstore=InMemoryDocstore())
        self.vs.save_local(str(self._index_dir()))

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.vs is None:
            self.load_or_build()
        assert self.vs is not None

        hits = self.vs.similarity_search_with_score(query, k=top_k)
        results = []
        for doc, score in hits:
            meta = dict(doc.metadata)
            results.append({
                "id": meta.get("id") or meta.get("vendor_id") or meta.get("name"),
                "title": meta.get("name"),
                "score": float(score),
                "snippet": doc.page_content[:240],
                "metadata": {k: v for k, v in meta.items() if k not in ("id", "name")},
            })
        return results

# シングルトン利用
_rag: VendorRAG | None = None

def get_rag() -> VendorRAG:
    global _rag
    if _rag is None:
        _rag = VendorRAG()
        _rag.load_or_build()
    return _rag

def search_vendors(query: str, top_k: int = 5):
    return get_rag().search(query, top_k)

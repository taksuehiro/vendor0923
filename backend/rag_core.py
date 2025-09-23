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
        
        # ファイル更新チェック
        should_rebuild = False
        if self._exists():
            # 既存インデックスの更新日時とデータファイルの更新日時を比較
            index_time = max(
                (self._index_dir() / "index.faiss").stat().st_mtime,
                (self._index_dir() / "index.pkl").stat().st_mtime
            )
            if DATA_PATH.exists():
                data_time = DATA_PATH.stat().st_mtime
                if data_time > index_time:
                    should_rebuild = True
                    print(f"📊 データファイルが更新されました。ベクトルストアを再構築します...")
            else:
                should_rebuild = True
        else:
            should_rebuild = True
            print(f"📊 ベクトルストアが見つかりません。新規構築します...")

        if not should_rebuild:
            print(f"📊 既存のベクトルストアを読み込みました: {self._index_dir()}")
            self.vs = FAISS.load_local(
                str(self._index_dir()),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
            return

        # データ読み込み（最低限のスキーマ: id, name, description, status, category）
        docs: List[Document] = []
        if DATA_PATH.exists():
            print(f"📊 データファイルを読み込み中: {DATA_PATH}")
            items = json.loads(DATA_PATH.read_text(encoding="utf-8"))
            print(f"📊 {len(items)}件のベンダーデータを読み込みました")
        else:
            print(f"⚠️  データファイルが見つかりません: {DATA_PATH}")
            # フォールバックのサンプル
            items = [
                {"id": "V-LiberCraft", "name": "LiberCraft", "description": "AI・機械学習を活用したスクラッチ開発サービス。契約書管理や法務業務の自動化に強み。", "status": "面談済", "category": "スクラッチ"},
                {"id": "V-TechCorp", "name": "TechCorp", "description": "クラウドインフラ構築・運用支援のSaaS。契約管理ワークフロー連携に実績。", "status": "未面談", "category": "SaaS"},
            ]
            print(f"📊 フォールバックデータ {len(items)}件を使用します")

        for it in items:
            # より詳細なテキスト生成
            name = it.get('name', '')
            description = it.get('description', '')
            status = it.get('status', '')
            category = it.get('category', '')
            
            # 検索に適したテキストを生成
            text_parts = [name]
            if description:
                text_parts.append(description)
            if status:
                text_parts.append(f"ステータス: {status}")
            if category:
                text_parts.append(f"カテゴリ: {category}")
            
            text = "。".join(text_parts)
            meta = {k: v for k, v in it.items() if k not in ("description",)}
            docs.append(Document(page_content=text, metadata=meta))

        print(f"📊 ベクトルストアを構築中...")
        # ベクトルストア作成
        self.vs = FAISS.from_documents(docs, self.embeddings, docstore=InMemoryDocstore())
        self.vs.save_local(str(self._index_dir()))
        print(f"📊 ベクトルストアを保存しました: {self._index_dir()}")

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.vs is None:
            self.load_or_build()
        assert self.vs is not None

        hits = self.vs.similarity_search_with_score(query, k=top_k)
        results = []
        for doc, score in hits:
            meta = dict(doc.metadata)
            # 必須フィールドを保証
            status = meta.get("status", "")
            category = meta.get("category", "")
            
            results.append({
                "id": meta.get("id") or meta.get("vendor_id") or meta.get("name"),
                "title": meta.get("name"),
                "score": float(score),
                "snippet": doc.page_content[:240],
                "metadata": {
                    "status": status,
                    "category": category
                },
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

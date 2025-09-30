# backend/rag_core.py
from __future__ import annotations
import os
import json
from pathlib import Path
from typing import List, Dict, Any

from rag_core.bedrock_embeddings import TitanEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_core.documents import Document
from backend.rag_core_s3 import exists_current, download_current_to, upload_to_staging, promote_staging_to_current

# 環境変数
VECTOR_DIR = Path(os.getenv("VECTOR_DIR", "/app/vectorstore")).resolve()
DATA_PATH = Path(os.getenv("VENDOR_DATA_JSON", "/app/data/vendors.json")).resolve()

INDEX_NAME = "vendors"

class VendorRAG:
    def __init__(self) -> None:
        self.embeddings = TitanEmbeddings()
        self.vs: FAISS | None = None
        self.vectorstore_source: str = "unknown"

    # 永続パス
    def _index_dir(self) -> Path:
        return VECTOR_DIR / INDEX_NAME

    def _exists(self) -> bool:
        p = self._index_dir()
        return (p / "index.faiss").exists() and (p / "index.pkl").exists()
    
    def _local_exists(self) -> bool:
        return self._exists()

    def load_or_build(self) -> None:
        VECTOR_DIR.mkdir(parents=True, exist_ok=True)
        
        # 1) まず S3 current を優先ダウンロード → ローカルに配置
        try:
            if os.getenv("VECTORSTORE_S3_BUCKET") and exists_current():
                print(f"📊 S3 current からベクトルストアをダウンロード中...")
                download_current_to(str(self._index_dir()))
                print(f"📊 S3 current からダウンロード完了: {self._index_dir()}")
        except Exception as e:
            print(f"⚠️  S3 current load skipped: {e}")

        # 2) ローカルVECTOR_DIRに既存があれば読み込み
        if self._local_exists():
            print(f"📊 既存のベクトルストアを読み込みました: {self._index_dir()}")
            self.vs = FAISS.load_local(
                str(self._index_dir()),
                self.embeddings,
                allow_dangerous_deserialization=True,
            )
            self.vectorstore_source = "S3/current" if os.getenv("VECTORSTORE_S3_BUCKET") else "local-cache"
            return

        # 3) なければ vendors.json を見て再構築（従来通り）
        should_rebuild = True
        print(f"📊 ベクトルストアが見つかりません。新規構築します...")

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
        
        # 3.1) S3 が設定されていれば staging にアップロード → current へ昇格
        if os.getenv("VECTORSTORE_S3_BUCKET"):
            try:
                staging = upload_to_staging(str(self._index_dir()))
                promote_staging_to_current(staging)
                self.vectorstore_source = "rebuilt->S3/current"
                print(f"📊 ベクトルストアをS3 currentに昇格しました")
            except Exception as e:
                print(f"⚠️  S3 promote failed (using rebuilt local): {e}")
                self.vectorstore_source = "rebuilt"
        else:
            self.vectorstore_source = "rebuilt"

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

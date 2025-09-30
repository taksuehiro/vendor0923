# rag_core/indexer.py
from __future__ import annotations
import re
from pathlib import Path
from typing import Iterable, List, Optional

from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from rag_core.bedrock_embeddings import TitanEmbeddings
import os
import logging

from rag_core.loaders.json_loader import load_json_as_documents

log = logging.getLogger(__name__)

# 既存 splitter.py の関数をインポート
def _import_md_splitter():
    try:
        from splitter import make_splits
        from rag_core.loader import load_md
        return make_splits, load_md
    except Exception as e:
        print(f"Warning: Could not import splitter functions: {e}")
        return None, None

_MD_SPLITTER, _MD_LOADER = _import_md_splitter()

def _ascii_safe(s: str) -> str:
    # Windows/Unix両対応の安全なディレクトリ名生成
    s = re.sub(r"[^\w\-.]+", "_", s, flags=re.UNICODE)
    return s[:80] if len(s) > 80 else s

def load_documents_auto(path: Path, chunk_size: int = 0, chunk_overlap: int = 0) -> List[Document]:
    if not path.exists():
        raise FileNotFoundError(f"Not found: {path}")
    suffix = path.suffix.lower()
    if suffix == ".json":
        return load_json_as_documents(path, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    elif suffix in (".md", ".markdown"):
        if _MD_SPLITTER is None or _MD_LOADER is None:
            raise RuntimeError("Markdown分割機能が見つかりません（splitter.py を確認）")
        # 既存のload_md + make_splitsの組み合わせを使用
        raw_docs = _MD_LOADER([str(path)])
        return _MD_SPLITTER(raw_docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

def find_best_data_file(data_dir: Path) -> Path:
    """JSON優先で自動選択：1) vendors.json → 2) ベンダー調査JSON練習版.json → 3) ベンダー調査.json → 4) 任意の .json → 5) .md/.markdown"""
    # 1) vendors.json（最優先）
    target = data_dir / "vendors.json"
    if target.exists():
        return target
    
    # 2) ベンダー調査JSON練習版.json
    target = data_dir / "ベンダー調査JSON練習版.json"
    if target.exists():
        return target
    
    # 3) ベンダー調査.json
    target = data_dir / "ベンダー調査.json"
    if target.exists():
        return target
    
    # 4) 任意の .json
    jsons = sorted(data_dir.glob("*.json"))
    if jsons:
        return jsons[0]
    
    # 5) .md / .markdown
    mds = sorted([p for p in data_dir.glob("*.md")] + [p for p in data_dir.glob("*.markdown")])
    if mds:
        return mds[0]
    
    raise FileNotFoundError(f"No data files found in {data_dir}")

def load_documents_from_dir(dir_path: Path, chunk_size: int = 0, chunk_overlap: int = 0) -> List[Document]:
    """フォルダ指定時は拡張子で自動判定。**同名のMDとJSONがある場合はJSONを優先**。"""
    jsons = sorted(dir_path.glob("*.json"))
    mds   = sorted([p for p in dir_path.glob("*.md")] + [p for p in dir_path.glob("*.markdown")])

    # 同名優先（stem一致はJSONのみ採用）
    md_map = {p.stem: p for p in mds}
    paths: List[Path] = []
    used_stems = set()
    for j in jsons:
        paths.append(j)
        used_stems.add(j.stem)
    for m in mds:
        if m.stem not in used_stems:
            paths.append(m)

    docs: List[Document] = []
    for p in paths:
        docs.extend(load_documents_auto(p, chunk_size=chunk_size, chunk_overlap=chunk_overlap))
    return docs

def build_faiss(
    documents: Iterable[Document],
    embeddings: Optional[TitanEmbeddings] = None,
    out_dir: Optional[Path] = None
) -> FAISS:
    if embeddings is None:
        embeddings = TitanEmbeddings()
    vs = FAISS.from_documents(list(documents), embeddings)
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        safe = _ascii_safe(str(out_dir))
        vs.save_local(out_dir / safe)  # save_localはディレクトリを受け取る
        
        # S3 が設定されていれば staging にアップロード → current へ昇格
        if os.getenv("VECTORSTORE_S3_BUCKET"):
            try:
                from rag_core_s3 import upload_to_staging, promote_staging_to_current
                staging = upload_to_staging(str(out_dir / safe))
                promote_staging_to_current(staging)
                log.info("Vectorstore promoted to S3 current")
            except Exception as e:
                log.warning(f"S3 promote failed after rebuild: {e}")
    return vs
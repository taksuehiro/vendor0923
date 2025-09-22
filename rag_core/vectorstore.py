import os
import tempfile
from pathlib import Path
from typing import Optional, List, Tuple
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

def _ascii_fallback_dir() -> str:
    base = Path(os.getenv("LOCALAPPDATA", tempfile.gettempdir()))
    p = base / "vendor0922" / "vectorstore"
    p.mkdir(parents=True, exist_ok=True)
    return str(p.resolve())

def _sanitize_docs(docs: List[Document]) -> List[Document]:
    """空ドキュメントを除外してクリーンなリストを返す"""
    clean = []
    for d in docs:
        if d and isinstance(d, Document):
            txt = (d.page_content or "").strip()
            if txt:
                # metadataがNoneなら空dictに
                if d.metadata is None:
                    d.metadata = {}
                clean.append(Document(page_content=txt, metadata=d.metadata))
    return clean

def load_vectorstore(persist_dir: str, embeddings) -> Tuple[Optional[FAISS], Optional[str]]:
    """指定persist_dirで読めればそこを、ダメならフォールバック先を試す。実際に使ったdirを返す。"""
    p = Path(persist_dir)
    if p.exists() and any(p.iterdir()):
        vs = FAISS.load_local(str(p), embeddings, allow_dangerous_deserialization=True)
        return vs, str(p.resolve())

    # フォールバック先に既存があれば使う
    fb = _ascii_fallback_dir()
    q = Path(fb)
    if q.exists() and any(q.iterdir()):
        vs = FAISS.load_local(str(q), embeddings, allow_dangerous_deserialization=True)
        return vs, fb

    return None, None

def build_vectorstore(splits: List[Document], embeddings, persist_dir: str) -> Tuple[FAISS, str]:
    """保存に失敗したらフォールバックへ保存。実際に保存したdirを返す。"""
    splits = _sanitize_docs(splits)
    if not splits:
        raise ValueError(
            "分割結果が0件でした。セパレータ書式（例: '### ベンダー n:'）や入力ファイル内容を確認してください。"
            "（chunk_size=0 の場合はベンダー単位、>0 の場合は長文のみ二次分割）"
        )

    vs = FAISS.from_documents(splits, embeddings)
    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    try:
        vs.save_local(persist_dir)
        return vs, str(Path(persist_dir).resolve())
    except Exception as e:
        msg = str(e)
        if ("Illegal byte sequence" in msg) or ("could not open" in msg) or ("FileIOWriter" in msg):
            fb = _ascii_fallback_dir()
            vs.save_local(fb)
            return vs, fb
        raise

def build_or_load_vectorstore(
    docs: List[Document],
    embeddings,
    persist_dir: str,
    chunk_size: int,
    chunk_overlap: int,
    splitter_fn,
) -> Tuple[FAISS, bool, str]:
    """既存があればロード、なければ作成。 (vectorstore, created, used_dir) を返す。"""
    vs, used_dir = load_vectorstore(persist_dir, embeddings)
    if vs:
        return vs, False, used_dir

    splits = splitter_fn(docs, chunk_size, chunk_overlap)
    vs, used_dir = build_vectorstore(splits, embeddings, persist_dir)
    return vs, True, used_dir
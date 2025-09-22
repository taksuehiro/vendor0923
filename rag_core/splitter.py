"""
Markdown専用のベンダー分割モジュール

このモジュールは Markdown 形式のベンダー調査データ（### ベンダー n: 形式）を
ベンダー単位で分割するために使用されます。

source_format メタデータが "md" のときのみ使用してください。
JSON形式のデータには使用しないでください。
"""
import re, unicodedata
from typing import List, Tuple, Dict
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

HEADER_RE = re.compile(r'(?m)^#{2,4}\s*ベンダー\s*\d+\s*[:：]')

def _normalize(text: str) -> str:
    t = unicodedata.normalize("NFKC", text)
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    return t

def split_by_vendor(content: str) -> List[str]:
    text = _normalize(content)
    positions = [m.start() for m in HEADER_RE.finditer(text)]
    if not positions:
        return [text.strip()] if text.strip() else []
    blocks = []
    for i, start in enumerate(positions):
        end = positions[i+1] if i+1 < len(positions) else len(text)
        block = text[start:end].strip()
        if block:
            blocks.append(block)
    return blocks

def _extract_metadata(content: str) -> Dict[str, str]:
    meta = {}
    first_line = content.splitlines()[0] if content else ""
    m = re.match(r'^#{2,4}\s*ベンダー\s*\d+\s*[:：]\s*([^｜\|]+)', first_line)
    if m:
        meta["vendor_name"] = m.group(1).strip()
    m2 = re.search(r'ベンダーID\s*[:：]\s*([^\s｜\|]+)', content)
    if m2:
        meta["vendor_id"] = m2.group(1).strip()
    return meta

def vendor_first_then_chunk(docs: List[Document], chunk_size: int, chunk_overlap: int) -> Tuple[List[Document], Dict]:
    out: List[Document] = []
    stats = {"vendors": 0, "overlong_blocks": 0, "invalid": 0}
    for d in docs:
        blocks = split_by_vendor(d.page_content or "")
        for b in blocks:
            meta = d.metadata.copy()
            vendor_meta = _extract_metadata(b)
            meta.update(vendor_meta)
            if "vendor_name" not in meta:
                stats["invalid"] += 1
            stats["vendors"] += 1
            if chunk_size == 0:
                out.append(Document(page_content=b, metadata=meta))
            elif len(b) > chunk_size:
                ts = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=max(chunk_overlap, 0))
                for p in ts.split_text(b):
                    if p.strip():
                        out.append(Document(page_content=p.strip(), metadata=meta))
                stats["overlong_blocks"] += 1
            else:
                out.append(Document(page_content=b, metadata=meta))
    return out, stats

def make_splits(docs: List[Document], chunk_size: int, chunk_overlap: int) -> List[Document]:
    docs2, _ = vendor_first_then_chunk(docs, chunk_size, chunk_overlap)
    return docs2
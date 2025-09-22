import os
from typing import List
from langchain_community.document_loaders import TextLoader
from langchain.schema import Document

def load_md(md_paths: List[str]) -> List[Document]:
    docs: List[Document] = []
    for p in md_paths:
        if os.path.exists(p):
            loader = TextLoader(p, encoding="utf-8")
            d = loader.load()
            for i, doc in enumerate(d):
                doc.metadata.update({"file_path": p, "chunk_id": i, "source": "vendors_md"})
            docs.extend(d)
        else:
            raise FileNotFoundError(f"Not found: {p}")
    return docs
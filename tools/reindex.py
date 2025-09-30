# tools/reindex.py
import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv
from rag_core.bedrock_embeddings import TitanEmbeddings

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from rag_core.indexer import load_documents_auto, load_documents_from_dir, build_faiss

def main():
    load_dotenv()  # .env の OPENAI_API_KEY を読み込み
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="ファイル(.json/.md) または ディレクトリ")
    ap.add_argument("--chunk_size", type=int, default=0)
    ap.add_argument("--chunk_overlap", type=int, default=0)
    ap.add_argument("--out_dir", default=".vectorstores/vendors_faiss")
    args = ap.parse_args()

    path = Path(args.input)
    if path.is_dir():
        docs = load_documents_from_dir(path, chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)
    else:
        docs = load_documents_auto(path, chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)

    print(f"[reindex] docs: {len(docs)}")
    vs = build_faiss(docs, embeddings=TitanEmbeddings(), out_dir=Path(args.out_dir))
    print(f"[reindex] saved to: {args.out_dir}")

if __name__ == "__main__":
    main()
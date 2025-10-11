# backend/build_faiss_index.py
import os
import json
from pathlib import Path
import boto3
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import BedrockEmbeddings
from langchain_community.docstore.document import Document

def build_faiss_index():
    # ====== 設定 ======
    bucket = os.getenv("S3_BUCKET_NAME", "vendor-rag-bucket")
    prefix = os.getenv("S3_PREFIX", "vectorstore/prod")  # ロード側と統一
    region = os.getenv("AWS_REGION", "ap-northeast-1")
    model_id = os.getenv("BEDROCK_EMBEDDINGS_MODEL_ID", "amazon.titan-embed-text-v1")
    local_dir = "/tmp/vectorstore"

    Path(local_dir).mkdir(parents=True, exist_ok=True)

    # ====== データ読み込み ======
    data_path = Path(__file__).parent / "data" / "vendors.json"
    with open(data_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    docs = []
    for r in records:
        text = f"{r.get('name', '')}\n{r.get('description', '')}"
        meta = {k: v for k, v in r.items() if k not in ("name", "description")}
        docs.append(Document(page_content=text, metadata=meta))

    print(f"✅ Loaded {len(docs)} documents from {data_path}")

    # ====== Embeddings作成 ======
    embeddings = BedrockEmbeddings(model_id=model_id, region_name=region)

    # ====== FAISSベクトルストア構築 ======
    print("🔍 Building FAISS index ...")
    vs = FAISS.from_documents(docs, embeddings)
    vs.save_local(local_dir)
    print(f"✅ Saved FAISS index to {local_dir}")

    # ====== S3にアップロード ======
    s3 = boto3.client("s3", region_name=region)
    for filename in ["index.faiss", "index.pkl"]:
        local_path = f"{local_dir}/{filename}"
        s3_path = f"{prefix}/{filename}"
        s3.upload_file(local_path, bucket, s3_path)
        print(f"📤 Uploaded {filename} to s3://{bucket}/{s3_path}")

    print("🎉 All done! FAISS index is now available on S3.")

if __name__ == "__main__":
    build_faiss_index()

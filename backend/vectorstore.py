"""
S3からFAISSインデックスをロードするモジュール
"""
import os
import tempfile
import shutil
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import BedrockEmbeddings

# 環境変数
S3_BUCKET = os.environ.get("S3_BUCKET", "vendor-rag-0919")
S3_PREFIX = os.environ.get("S3_PREFIX", "vectorstore/prod")
AWS_REGION = os.environ.get("AWS_REGION", "ap-northeast-1")
BEDROCK_REGION = os.environ.get("BEDROCK_REGION", AWS_REGION)
EMBED_MODEL_ID = os.environ.get("BEDROCK_EMBED_MODEL", "amazon.titan-embed-text-v2:0")

# グローバル変数
VSTORE = None

def _init_embeddings():
    """BedrockEmbeddingsを初期化"""
    return BedrockEmbeddings(
        model_id=EMBED_MODEL_ID,
        region_name=BEDROCK_REGION,
    )

def load_vectorstore():
    """
    S3からFAISSインデックスをダウンロードしてロードする
    
    Returns:
        FAISS: ロードされたベクトルストア
    """
    global VSTORE
    
    if VSTORE is not None:
        return VSTORE
    
    s3 = boto3.resource("s3", region_name=AWS_REGION)
    bucket = s3.Bucket(S3_BUCKET)
    
    # 一時ディレクトリを作成
    tmpdir = tempfile.mkdtemp(prefix="faiss_")
    local_dir = os.path.join(tmpdir, "faiss")
    os.makedirs(local_dir, exist_ok=True)
    
    try:
        # S3からファイルをダウンロード
        prefix = S3_PREFIX.rstrip("/") + "/"
        for obj in bucket.objects.filter(Prefix=prefix):
            rel = obj.key[len(prefix):]
            if rel == "" or rel.endswith("/"):
                continue
            dst_path = os.path.join(local_dir, rel)
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            bucket.download_file(obj.key, dst_path)
            
    except ClientError as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"S3 download error: {e}")
    
    try:
        # FAISSをロード
        VSTORE = FAISS.load_local(
            folder_path=local_dir,
            embeddings=_init_embeddings(),
            allow_dangerous_deserialization=True,
        )
        
        # 一時ディレクトリをクリーンアップ
        shutil.rmtree(tmpdir, ignore_errors=True)
        
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"FAISS load error: {e}")
    
    return VSTORE

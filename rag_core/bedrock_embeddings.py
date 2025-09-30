# rag_core/bedrock_embeddings.py
import boto3
import json
from typing import List
import logging

log = logging.getLogger(__name__)

# Bedrock Runtime クライアントを初期化
bedrock = boto3.client("bedrock-runtime", region_name="ap-northeast-1")

def titan_embedding(text: str) -> List[float]:
    """
    Amazon Titan Embeddings を使用してテキストをベクトル化する
    """
    try:
        body = {"inputText": text}
        resp = bedrock.invoke_model(
            modelId="amazon.titan-embed-text-v2:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body),
        )
        result = json.loads(resp["body"].read())
        return result["embedding"]
    except Exception as e:
        log.error(f"Titan embedding failed: {e}")
        raise

def titan_embeddings(texts: List[str]) -> List[List[float]]:
    """
    複数のテキストを一括でベクトル化する
    """
    embeddings = []
    for text in texts:
        embeddings.append(titan_embedding(text))
    return embeddings

class TitanEmbeddings:
    """
    LangChain の Embeddings インターフェースに準拠した Titan Embeddings クラス
    """
    
    def __init__(self):
        self.model_name = "amazon.titan-embed-text-v2:0"
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """ドキュメントのリストをベクトル化"""
        return titan_embeddings(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """クエリテキストをベクトル化"""
        return titan_embedding(text)

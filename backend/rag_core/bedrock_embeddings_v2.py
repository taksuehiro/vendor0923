import json
import boto3
import os

class BedrockEmbeddingsV2:
    def __init__(self, model_id=None, region_name="ap-northeast-1"):
        self.model_id = model_id or os.getenv("BEDROCK_EMBEDDINGS_MODEL_ID", "amazon.titan-embed-text-v2")
        self.client = boto3.client("bedrock-runtime", region_name=region_name)

    def embed_query(self, text: str):
        body = {"inputText": text}  # ← Titan v2はこれ
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
        )
        data = json.loads(response["body"].read())
        return data["embedding"]

    def embed_documents(self, texts):
        return [self.embed_query(t) for t in texts]

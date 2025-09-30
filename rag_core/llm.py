from rag_core.bedrock_llm import TitanLLM
from rag_core.bedrock_embeddings import TitanEmbeddings

def get_embeddings(model_name: str = None, api_key: str = None):
    """
    Bedrock Titan Embeddings を返す（引数は互換性のため残すが使用しない）
    """
    return TitanEmbeddings()

def get_chat(model_name: str = None, temperature: float = None, api_key: str = None):
    """
    Bedrock Titan LLM を返す（引数は互換性のため残すが使用しない）
    """
    return TitanLLM()
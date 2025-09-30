# rag_core/bedrock_llm.py
import logging
from langchain_community.llms import Bedrock

log = logging.getLogger(__name__)

class TitanLLM:
    """
    Amazon Bedrock Titan Text G1 - Express を使用するLLMクラス
    """
    
    def __init__(self):
        try:
            self.llm = Bedrock(
                model_id="amazon.titan-text-express-v1",
                region_name="ap-northeast-1",
            )
            log.info("Bedrock Titan LLM initialized successfully")
        except Exception as e:
            log.error(f"Failed to initialize Bedrock Titan LLM: {e}")
            raise
    
    def invoke(self, prompt: str) -> str:
        """
        プロンプトを実行してレスポンスを取得
        """
        try:
            response = self.llm.invoke(prompt)
            return response
        except Exception as e:
            log.error(f"Bedrock Titan LLM invocation failed: {e}")
            raise
    
    def __call__(self, prompt: str) -> str:
        """
        直接呼び出し可能にする
        """
        return self.invoke(prompt)

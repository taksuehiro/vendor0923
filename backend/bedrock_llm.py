# backend/bedrock_llm.py
"""
Bedrock LLM統合モジュール
Claude 3 Haikuを使用したLLM操作を提供
"""
import json
import logging
import os
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

log = logging.getLogger(__name__)

# グローバルクライアント（シングルトン）
_bedrock_client = None


def get_bedrock_client():
    """Bedrockクライアントを取得（シングルトン）"""
    global _bedrock_client
    if _bedrock_client is not None:
        return _bedrock_client
    
    region = os.getenv("AWS_REGION", "ap-northeast-1")
    _bedrock_client = boto3.client("bedrock-runtime", region_name=region)
    log.info(f"Initialized Bedrock client in region: {region}")
    
    return _bedrock_client


class BedrockLLM:
    """
    Bedrock Claude 3 Haiku LLMラッパー
    
    Usage:
        llm = BedrockLLM()
        response = llm.invoke("こんにちは")
        print(response)
    """
    
    def __init__(
        self,
        model_id: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.0,
        top_p: float = 1.0
    ):
        """
        Args:
            model_id: BedrockモデルID（デフォルト：環境変数から取得）
            max_tokens: 最大トークン数
            temperature: 温度（0.0-1.0）
            top_p: Top-Pサンプリング（0.0-1.0）
        """
        self.client = get_bedrock_client()
        self.model_id = model_id or os.getenv(
            "BEDROCK_LLM_MODEL_ID",
            "anthropic.claude-3-haiku-20240307-v1:0"
        )
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        
        log.info(f"BedrockLLM initialized: model={self.model_id}")
    
    def invoke(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        LLMを呼び出して応答を取得
        
        Args:
            prompt: ユーザープロンプト
            system: システムプロンプト（オプション）
            max_tokens: 最大トークン数（オプション、デフォルトはインスタンス設定）
            temperature: 温度（オプション、デフォルトはインスタンス設定）
        
        Returns:
            str: LLMの応答テキスト
        """
        # リクエストボディを構築
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ],
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
            "top_p": self.top_p
        }
        
        # システムプロンプトがあれば追加
        if system:
            body["system"] = system
        
        try:
            # Bedrock呼び出し
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )
            
            # レスポンスをパース
            result = json.loads(response["body"].read())
            
            # テキストを抽出
            if "content" in result and len(result["content"]) > 0:
                text = result["content"][0]["text"]
                log.debug(f"LLM response: {text[:100]}...")
                return text
            else:
                log.warning(f"Unexpected response format: {result}")
                return ""
        
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            log.error(f"Bedrock ClientError: {error_code} - {error_message}")
            raise RuntimeError(f"Bedrock API error: {error_message}")
        
        except Exception as e:
            log.error(f"Unexpected error in BedrockLLM.invoke: {e}")
            raise
    
    def invoke_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs
    ) -> Dict:
        """
        LLMを呼び出してJSON形式の応答を取得
        
        Args:
            prompt: ユーザープロンプト
            system: システムプロンプト（オプション）
            **kwargs: invoke()に渡す追加引数
        
        Returns:
            dict: パースされたJSON応答
        """
        response_text = self.invoke(prompt, system=system, **kwargs)
        
        try:
            # ```json ... ``` のようなマークダウン形式を処理
            if "```json" in response_text:
                # ```json と ``` の間を抽出
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                # ``` だけの場合
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            
            return json.loads(response_text)
        
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse JSON from LLM response: {response_text}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")


def classify_query_with_llm(query: str) -> Dict[str, any]:
    """
    LLMを使用してクエリを分類
    
    Args:
        query: ユーザークエリ
    
    Returns:
        dict: {
            "type": "structured" | "hybrid" | "semantic",
            "filters": {"column": "value"},
            "semantic_query": "..."
        }
    """
    system_prompt = """あなたはベンダー検索システムのクエリ分類エージェントです。
ユーザークエリを分析して、以下の形式でJSON応答してください：

{
  "type": "structured" | "hybrid" | "semantic",
  "filters": {"column_name": "filter_value"},
  "semantic_query": "セマンティック検索部分"
}

フィルタ可能なカラム：
- engagement.status: "面談済" | "未面談"
- corporate.listed: "上場" | "未上場"
- type: "SaaS" | "スクラッチ" | "SI"

分類ルール：
- structured: フィルタのみで答えられる（例：「面談済みの会社」）
- hybrid: フィルタ + セマンティック検索が必要（例：「面談済みのチャットボット企業」）
- semantic: フィルタ不要、意味検索のみ（例：「AI活用に強い企業」）

必ずJSON形式のみで応答してください。説明文は不要です。"""
    
    user_prompt = f"以下のクエリを分類してください：\n\n{query}"
    
    try:
        llm = BedrockLLM(max_tokens=500, temperature=0.0)
        result = llm.invoke_json(user_prompt, system=system_prompt)
        
        log.info(f"LLM classification result: {result}")
        return result
    
    except Exception as e:
        log.warning(f"LLM classification failed, falling back to rule-based: {e}")
        # フォールバック：ルールベースに戻る
        return None


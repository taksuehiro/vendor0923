# Bedrock LLM統合ドキュメント

## 概要

このプロジェクトでは、AWS Bedrock経由でClaude 3 Haikuを使用できます。

## 設定

### 環境変数

```bash
# LLMモデルID（デフォルト：Claude 3 Haiku）
BEDROCK_LLM_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# LLMベースのクエリ分類を使用するか（デフォルト：false）
USE_LLM_CLASSIFICATION=false
```

### ECSタスク定義

`ecs_taskdef.json`に以下が設定済み：

```json
{ "name": "BEDROCK_LLM_MODEL_ID", "value": "anthropic.claude-3-haiku-20240307-v1:0" },
{ "name": "USE_LLM_CLASSIFICATION", "value": "false" }
```

## 使用方法

### 1. 基本的なLLM呼び出し

```python
from backend.bedrock_llm import BedrockLLM

# LLMインスタンス作成
llm = BedrockLLM()

# シンプルな呼び出し
response = llm.invoke("こんにちは、自己紹介してください")
print(response)

# システムプロンプト付き
response = llm.invoke(
    prompt="Pythonとは何ですか？",
    system="あなたは技術的な質問に答えるアシスタントです。簡潔に答えてください。",
    max_tokens=200
)
print(response)
```

### 2. JSON応答の取得

```python
# JSON形式で応答を取得
response = llm.invoke_json(
    prompt="以下の文章から重要な情報を抽出してJSONで返してください：\n\n株式会社サンプルは2020年に設立されました。",
    system="必ずJSON形式で応答してください。"
)
print(response)  # dict型
```

### 3. クエリ分類（Intent Classification）

```python
from backend.structured_search import classify_query

# ルールベースの分類（デフォルト）
search_type, filters, semantic = classify_query("面談済みの会社")
# → ("hybrid", {"engagement.status": "面談済"}, "会社")

# LLMベースの分類（より高度）
search_type, filters, semantic = classify_query("面談済みの会社", use_llm=True)
# → LLMが自然言語理解して分類
```

## LLM分類の有効化

### 開発環境

```bash
export USE_LLM_CLASSIFICATION=true
python -m uvicorn backend.main_app:app --reload
```

### 本番環境（ECS）

`ecs_taskdef.json`を編集：

```json
{ "name": "USE_LLM_CLASSIFICATION", "value": "true" }
```

## ルールベース vs LLMベースの比較

| 項目 | ルールベース | LLMベース |
|------|-------------|-----------|
| **速度** | 速い（< 1ms） | 遅い（100-500ms） |
| **コスト** | 無料 | Bedrock課金 |
| **精度** | 定義済みパターンのみ | 柔軟な自然言語理解 |
| **保守性** | 正規表現メンテナンス必要 | プロンプト調整で対応 |
| **言い換え対応** | 限定的 | 優れている |

**推奨：** まずはルールベース（デフォルト）で運用し、必要に応じてLLMを有効化

## モデル変更

別のClaudeモデルを使用する場合：

```bash
# Claude 3 Sonnet
BEDROCK_LLM_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Claude 3 Opus
BEDROCK_LLM_MODEL_ID=anthropic.claude-3-opus-20240229-v1:0
```

## トラブルシューティング

### AccessDeniedException

IAMロールに以下の権限が必要：

```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock:InvokeModel"
  ],
  "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-*"
}
```

### レスポンスが遅い

- Claude 3 Haikuは最速モデルですが、それでも100-500msかかります
- `max_tokens`を減らすと若干速くなります
- キャッシュの実装を検討してください

## API仕様

### BedrockLLM クラス

```python
class BedrockLLM:
    def __init__(
        self,
        model_id: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.0,
        top_p: float = 1.0
    )
    
    def invoke(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str
    
    def invoke_json(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs
    ) -> Dict
```

### パラメータ説明

- **max_tokens**: 最大出力トークン数（デフォルト：1000）
- **temperature**: ランダム性（0.0-1.0、デフォルト：0.0）
  - 0.0: 決定的な応答
  - 1.0: 多様性のある応答
- **top_p**: Top-Pサンプリング（0.0-1.0、デフォルト：1.0）

## 参考リンク

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Claude 3 Model Card](https://www.anthropic.com/news/claude-3-family)
- [Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)



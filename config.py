import os
from pathlib import Path

# パス
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
VECTOR_DIR = Path(os.getenv("VECTOR_DIR",str(ROOT_DIR / "vectorstore")))
PROMPT_PATH = ROOT_DIR / "prompts" / "answer_prompt.md"

# データファイル（複数追加OK）
MD_PATHS = [str(DATA_DIR / "ベンダー調査.md")]

# 分割パラメータ（UIから上書き可能）
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120

# 検索パラメータ（UIから上書き可能）
DEFAULT_TOP_K = 5
USE_MMR = False
SCORE_THRESHOLD = None  # 例: 0.2 で絞り込み

# モデル（Amazon Bedrock Titan使用）
EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"  # Bedrock Titan Embeddings
CHAT_MODEL = "amazon.titan-text-express-v1"  # Bedrock Titan Text
TEMPERATURE = 0.0
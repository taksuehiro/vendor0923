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

# モデル（UIから切替想定）
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI
CHAT_MODEL = "gpt-3.5-turbo"
TEMPERATURE = 0.0
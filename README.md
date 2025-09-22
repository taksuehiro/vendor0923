# ベンダー検索（ローカルRAG）

## 1. 依存インストール
pip install -r requirements.txt

shell
コードをコピーする

## 2. .env を作成
OPENAI_API_KEY=xxxxx

r
コードをコピーする

## 3. データを置く
- `data/ベンダー調査.md`（Windowsの元データパス：`C:\Users\TakuyaSuehiro\Desktop\AI市場調査\LangChain\vendor0922\data`）

## 4. 起動
streamlit run app_streamlit.py

markdown
コードをコピーする

## 5. チューニング
- サイドバーで `Top K / Chunk Size / Overlap / MMR / Score閾値 / Temperature / モデル` を調整
- プロンプトは `prompts/answer_prompt.md`
- 設定の初期値は `config.py`
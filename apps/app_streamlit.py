# apps/app_streamlit.py
from __future__ import annotations
from collections import Counter, defaultdict
from pathlib import Path
import os
import streamlit as st
from dotenv import load_dotenv

from langchain_community.vectorstores import FAISS
from rag_core.bedrock_embeddings import TitanEmbeddings

from rag_core.indexer import load_documents_auto, load_documents_from_dir, build_faiss

load_dotenv()
st.set_page_config(page_title="ベンダー検索（ローカルRAG, Streamlit）", page_icon="🔎", layout="wide")
st.markdown("# 🔎 ベンダー検索（ローカルRAG, Streamlit）")

# パス解決：apps/ から見て ../data を既定
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_JSON = DATA_DIR / "ベンダー調査JSON練習版.json"
DEFAULT_VS_DIR = PROJECT_ROOT / ".vectorstores" / "vendors_faiss"

with st.sidebar:
    st.subheader("データ読み込み")
    inp = st.text_input("入力（.json/.md または ディレクトリ）", str(DEFAULT_JSON))
    chunk_size = st.number_input("chunk_size（JSONは通常0）", min_value=0, max_value=4000, value=0, step=50)
    chunk_overlap = st.number_input("chunk_overlap", min_value=0, max_value=1000, value=0, step=10)
    do_load = st.button("読み込む / 再インデックス", use_container_width=True)

def _summarize(docs):
    by_status = Counter([d.metadata.get("status","-") for d in docs])
    by_cat = Counter([d.metadata.get("category","-") for d in docs])
    return by_status, by_cat.most_common(10)

@st.cache_resource(show_spinner=False)
def _emb():
    return TitanEmbeddings()

def _build_or_load_vectorstore(docs):
    DEFAULT_VS_DIR.mkdir(parents=True, exist_ok=True)
    vs = build_faiss(docs, embeddings=_emb(), out_dir=DEFAULT_VS_DIR)
    return vs

if do_load or "docs" not in st.session_state:
    try:
        p = Path(inp).expanduser()
        if p.is_dir():
            docs = load_documents_from_dir(p, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        else:
            docs = load_documents_auto(p, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        st.session_state["docs"] = docs
        st.success(f"読み込み成功: {p}（{len(docs)} ドキュメント）")
        st.session_state["vs"] = _build_or_load_vectorstore(docs)
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")

docs = st.session_state.get("docs", [])
vs = st.session_state.get("vs", None)

# --- KBビューア ---
with st.expander("📚 KBビューア（件数サマリ・欠損チェック・一覧）", expanded=True):
    st.markdown(f"- 総件数: **{len(docs)}**")
    by_status, top_cat = _summarize(docs)
    st.markdown("**ステータス内訳**: " + ", ".join([f"{k}: {v}" for k,v in by_status.items()]) or "-")
    st.markdown("**カテゴリ上位**: " + ", ".join([f"{k}: {v}" for k,v in top_cat]) or "-")

    # 欠損
    missing = defaultdict(list)
    for i, d in enumerate(docs):
        for key in ("vendor_id","name","category","status"):
            if not d.metadata.get(key):
                missing[key].append(i)
    if missing:
        st.warning("メタデータ欠損: " + ", ".join([f"{k}={len(v)}件" for k,v in missing.items()]))
    else:
        st.info("メタデータ欠損なし")

    # 一覧
    for i, d in enumerate(docs[:50]):  # 表示上限
        st.markdown(f"**#{i+1} {d.metadata.get('vendor_id')} — {d.metadata.get('name')}**")
        st.caption(f"{d.metadata.get('category')} / {', '.join(d.metadata.get('industry_tags', [])) or '-'}")
        st.code(d.page_content[:800])

st.divider()

# --- 検索 ---
st.subheader("🔎 検索")
q = st.text_input("クエリ（例：契約書 管理 法務 / 画像検査 製造 など）", "")
topk = st.slider("TopK", min_value=1, max_value=20, value=8)
if st.button("検索する", use_container_width=True):
    if not vs:
        st.error("ベクトルストア未構築です。左の『読み込む / 再インデックス』を実行してください。")
    else:
        try:
            retriever = vs.as_retriever(search_kwargs={"k": topk})
            results = retriever.get_relevant_documents(q)
            st.markdown(f"**検索結果: {len(results)} 件（上位 {topk}）**")
            for i, r in enumerate(results):
                md = r.metadata
                st.markdown(f"**#{i+1} {md.get('vendor_id')} — {md.get('name')}**")
                st.caption(f"{md.get('category')} / {', '.join(md.get('industry_tags', [])) or '-'} / {md.get('status')}")
                st.code(r.page_content[:1200])
        except Exception as e:
            st.error(f"検索エラー: {e}")



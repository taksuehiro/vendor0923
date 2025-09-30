import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import os

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag_core.vectorstore import load_vectorstore
from rag_core.llm import get_embeddings
from rag_core.indexer import resolve_openai_key

def safe_secret(name: str, default: str = "") -> str:
    """secrets.toml が無い場合でも例外にしない安全アクセサ"""
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default

def resolve_openai_key() -> str:
    # 優先順: session_state > env > secrets(あれば)
    key = (
        st.session_state.get("OPENAI_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or safe_secret("OPENAI_API_KEY", "")
    )
    return (key or "").strip().strip('"').strip("'")

def main():
    st.set_page_config(page_title="KBビューア", page_icon="📚", layout="wide")
    st.title("📚 ナレッジベースビューア")
    
    # 設定
    with st.sidebar:
        st.header("⚙️ 設定")
        
        st.info("Amazon Bedrock Titan を使用します（API Key不要）")
        
        # ベクトルストアディレクトリ設定
        vector_dir = st.text_input(
            "ベクトルストアディレクトリ",
            value=str(project_root / "vectorstore"),
            help="FAISSベクトルストアの保存先"
        )
    
    # Bedrock サービスを使用（API Key不要）
    st.caption("Amazon Bedrock Titan を使用中...")
    
    # ベクトルストアの読み込み
    try:
        embeddings = get_embeddings()
        vectorstore, used_dir = load_vectorstore(vector_dir, embeddings)
        
        if vectorstore is None:
            st.error(f"ベクトルストアが見つかりません: {vector_dir}")
            st.info("先にベクトルストアを作成してください。")
            st.stop()
            
    except Exception as e:
        st.error(f"ベクトルストア読み込みエラー: {e}")
        st.stop()
    
    # ドキュメントの取得
    try:
        # 全ドキュメントを取得（類似度検索で空文字列を指定）
        all_docs = vectorstore.similarity_search("", k=vectorstore.index.ntotal)
        
        if not all_docs:
            st.warning("ドキュメントが見つかりません。")
            st.stop()
            
    except Exception as e:
        st.error(f"ドキュメント取得エラー: {e}")
        st.stop()
    
    # サマリ情報の計算
    total_vendors = len(all_docs)
    
    # ステータス別件数
    status_counts = {}
    category_counts = {}
    source_format_counts = {}
    missing_vendor_id = 0
    
    for doc in all_docs:
        meta = doc.metadata
        
        # ステータス別集計
        status = meta.get("status", "不明")
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # カテゴリ別集計
        category = meta.get("category", "不明")
        category_counts[category] = category_counts.get(category, 0) + 1
        
        # ソース形式別集計
        source_format = meta.get("source_format", "不明")
        source_format_counts[source_format] = source_format_counts.get(source_format, 0) + 1
        
        # vendor_id欠落チェック
        if not meta.get("vendor_id"):
            missing_vendor_id += 1
    
    # サマリ表示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総ベンダー数", total_vendors)
    
    with col2:
        st.metric("vendor_id欠落", missing_vendor_id)
    
    with col3:
        st.metric("JSON形式", source_format_counts.get("json", 0))
    
    with col4:
        st.metric("Markdown形式", source_format_counts.get("md", 0))
    
    # ステータス別件数
    st.subheader("📊 ステータス別件数")
    status_df = pd.DataFrame(list(status_counts.items()), columns=["ステータス", "件数"])
    status_df = status_df.sort_values("件数", ascending=False)
    st.dataframe(status_df, use_container_width=True)
    
    # カテゴリ上位
    st.subheader("📊 カテゴリ上位")
    category_df = pd.DataFrame(list(category_counts.items()), columns=["カテゴリ", "件数"])
    category_df = category_df.sort_values("件数", ascending=False)
    st.dataframe(category_df, use_container_width=True)
    
    # フィルタ
    st.subheader("🔍 フィルタ")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_status = st.multiselect(
            "ステータス",
            options=list(status_counts.keys()),
            default=list(status_counts.keys())
        )
    
    with col2:
        selected_category = st.multiselect(
            "カテゴリ",
            options=list(category_counts.keys()),
            default=list(category_counts.keys())
        )
    
    with col3:
        selected_source_format = st.multiselect(
            "ソース形式",
            options=list(source_format_counts.keys()),
            default=list(source_format_counts.keys())
        )
    
    # フィルタ適用
    filtered_docs = []
    for doc in all_docs:
        meta = doc.metadata
        if (meta.get("status", "不明") in selected_status and
            meta.get("category", "不明") in selected_category and
            meta.get("source_format", "不明") in selected_source_format):
            filtered_docs.append(doc)
    
    st.info(f"フィルタ結果: {len(filtered_docs)}件 / {total_vendors}件")
    
    # ドキュメント一覧
    st.subheader("📋 ドキュメント一覧")
    
    for i, doc in enumerate(filtered_docs):
        meta = doc.metadata
        
        with st.expander(f"{i+1}. {meta.get('name', 'Unknown')} ({meta.get('vendor_id', 'No ID')})", expanded=False):
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.markdown("**メタデータ:**")
                st.json(meta)
            
            with col2:
                st.markdown("**内容プレビュー:**")
                content = doc.page_content
                st.text(content[:500] + ("..." if len(content) > 500 else ""))
                
                # vendor_idクリック可能
                vendor_id = meta.get("vendor_id")
                if vendor_id:
                    if st.button(f"🔍 {vendor_id} で検索", key=f"search_{i}"):
                        st.session_state[f"search_query_{i}"] = vendor_id
                
                # 検索結果表示
                if f"search_query_{i}" in st.session_state:
                    query = st.session_state[f"search_query_{i}"]
                    try:
                        search_results = vectorstore.similarity_search(query, k=3)
                        st.markdown(f"**「{query}」の検索結果:**")
                        for j, result in enumerate(search_results):
                            with st.expander(f"結果 {j+1}", expanded=False):
                                st.text(result.page_content[:300] + ("..." if len(result.page_content) > 300 else ""))
                    except Exception as e:
                        st.error(f"検索エラー: {e}")

if __name__ == "__main__":
    main()



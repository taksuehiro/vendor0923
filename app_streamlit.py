from pathlib import Path
from dotenv import load_dotenv
import os
import streamlit as st
import pandas as pd
from collections import Counter, defaultdict

ROOT = Path(__file__).parent
load_dotenv(dotenv_path=ROOT / ".env", override=False)

def safe_secret(name: str, default: str = "") -> str:
    """secrets.toml が無い場合でも例外にしない安全アクセサ"""
    try:
        return st.secrets.get(name, default)  # type: ignore[attr-defined]
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

import shutil

import config
from rag_core.loader import load_md
from rag_core.splitter import make_splits
from rag_core.vectorstore import build_or_load_vectorstore
from rag_core.llm import get_embeddings, get_chat
from rag_core.chain import load_prompt, make_chain
from rag_core.indexer import find_best_data_file, load_documents_auto, load_documents_from_dir, build_faiss

def read_prompt_file(path: Path) -> str:
    if not path.exists():
        return "【文脈】\n{context}\n\n【質問】\n{question}\n\n【回答】"
    return path.read_text(encoding="utf-8")

def _to_safe_list(x):
    """値を安全なリストに変換"""
    if isinstance(x, list): 
        return x
    if x is None: 
        return []
    return [x]

def build_kb_index(docs):
    """docs から集計とインデックスを作る"""
    by_id = {}
    facets = {
        "status": Counter(),
        "listed": Counter(),
        "type": Counter(),
        "use_cases": Counter(),
    }
    # 集計と基礎辞書
    for d in docs:
        m = d.metadata or {}
        vid = m.get("vendor_id") or m.get("name")
        if not vid: 
            continue
        by_id[vid] = {
            "vendor_id": vid,
            "name": m.get("name"),
            "status": m.get("status") or "不明",
            "listed": m.get("listed") or "不明",
            "type": m.get("type") or "その他",
            "use_cases": _to_safe_list(m.get("use_cases")),
            "url": m.get("url"),
            "employees_band": m.get("employees_band"),
            "investors": _to_safe_list(m.get("investors")),
            "is_scratch": m.get("is_scratch"),
            "category": m.get("category"),
            "deployment": m.get("deployment"),
            "price_range": m.get("price_range"),
            # 詳細表示用
            "industries": _to_safe_list(m.get("industries")),
            "departments": _to_safe_list(m.get("departments")),
            "doc": d,
        }
        facets["status"][by_id[vid]["status"]] += 1
        facets["listed"][by_id[vid]["listed"]] += 1
        facets["type"][by_id[vid]["type"]] += 1
        for u in by_id[vid]["use_cases"]:
            facets["use_cases"][u] += 1
    return by_id, facets

def render_summary_cards(facets):
    """クリック可能な集計カード群。クリックされたら state に保存"""
    st.subheader("集計（クリックでドリルダウン）")
    c1, c2, c3 = st.columns(3)

    # 面談ステータス
    with c1:
        st.caption("面談ステータス")
        cols = st.columns(max(1, len(facets["status"])))
        for i, (k, v) in enumerate(facets["status"].most_common()):
            if cols[i].button(f"{k}：{v}社", key=f"btn_status_{k}"):
                st.session_state["browse_clicked"] = ("status", k)

    # 上場区分
    with c2:
        st.caption("上場区分")
        cols = st.columns(max(1, len(facets["listed"])))
        for i, (k, v) in enumerate(facets["listed"].most_common()):
            if cols[i].button(f"{k}：{v}社", key=f"btn_listed_{k}"):
                st.session_state["browse_clicked"] = ("listed", k)

    # タイプ
    with c3:
        st.caption("タイプ")
        cols = st.columns(max(1, len(facets["type"])))
        for i, (k, v) in enumerate(facets["type"].most_common()):
            if cols[i].button(f"{k}：{v}社", key=f"btn_type_{k}"):
                st.session_state["browse_clicked"] = ("type", k)

def render_vendor_list(by_id, filters, clicked=None):
    """フィルタとクリック条件から一覧を出す"""
    def match(v):
        # status
        if filters["status"] and v["status"] not in filters["status"]:
            return False
        # listed
        if filters["listed"] and v["listed"] not in filters["listed"]:
            return False
        # type
        if filters["type"] and v["type"] not in filters["type"]:
            return False
        # use_cases (ANDではなくORマッチ)
        if filters["use_cases"]:
            if not set(v["use_cases"]).intersection(filters["use_cases"]):
                return False
        # カードクリックの絞り
        if clicked:
            key, val = clicked
            if key == "use_cases":
                return val in v["use_cases"]
            return v.get(key) == val
        return True

    rows = [v for v in by_id.values() if match(v)]
    rows = sorted(rows, key=lambda x: (x["status"] != "面談済", x["name"] or ""))  # 面談済を上に

    st.markdown(f"**該当：{len(rows)}社**")
    for v in rows:
        with st.expander(f"{v['name']} 〔{v['status']} / {v['listed']} / {v['type']}〕", expanded=False):
            st.markdown(f"- **Vendor ID**: `{v['vendor_id']}`")
            st.markdown(f"- **URL**: {v['url'] or '-'}")
            st.markdown(f"- **得意分野**: {', '.join(v['use_cases']) or '-'}")
            st.markdown(f"- **業界**: {', '.join(v['industries']) or '-'}")
            st.markdown(f"- **部門**: {', '.join(v['departments']) or '-'}")
            st.markdown(f"- **デプロイ**: {v['deployment'] or '-'}  / **価格帯**: {v['price_range'] or '-'}")
            st.markdown(f"- **従業員規模**: {v['employees_band'] or '-'}  / **投資家**: {', '.join(v['investors']) or '-'}")
            # 右（下）側で本文プレビュー
            st.code(v["doc"].page_content[:1200], language="markdown")

def browse_tab(docs):
    """ブラウズタブのメイン処理"""
    if not docs:
        st.warning("ドキュメントが読み込まれていません。先にインデックスを作成してください。")
        return
    by_id, facets = build_kb_index(docs)

    # フィルタ UI
    with st.sidebar:
        st.subheader("ブラウズ：フィルタ")
        f_status = st.multiselect("面談ステータス", options=list(facets["status"].keys()), default=[])
        f_listed = st.multiselect("上場区分", options=list(facets["listed"].keys()), default=[])
        f_type = st.multiselect("タイプ", options=list(facets["type"].keys()), default=[])
        f_use = st.multiselect("得意分野（use_cases）", options=list(facets["use_cases"].keys()), default=[])
        if st.button("フィルタをクリア"):
            f_status, f_listed, f_type, f_use = [], [], [], []
            st.session_state.pop("browse_clicked", None)

    # 集計カード（クリック対応）
    render_summary_cards(facets)

    clicked = st.session_state.get("browse_clicked")  # 例: ("status","未面談")
    if clicked:
        key, val = clicked
        st.info(f"ドリルダウン：{key} = {val}")

    # 一覧
    render_vendor_list(
        by_id,
        filters={"status": f_status, "listed": f_listed, "type": f_type, "use_cases": f_use},
        clicked=clicked
    )

def main():
    st.set_page_config(page_title="ベンダー検索（ローカルRAG）", page_icon="🔎", layout="wide")
    st.title("🔎 ベンダー検索（ローカルRAG, Streamlit）")
    st.caption("KEY head: " + (resolve_openai_key()[:10] if resolve_openai_key() else ""))

    # Sidebar - 調整UI
    with st.sidebar:
        st.header("⚙️ パラメータ")

        current_key = resolve_openai_key()
        api_key_input = st.text_input("OpenAI API Key（必要なら入力）", type="password", value=current_key)
        if api_key_input and api_key_input != current_key:
            st.session_state["OPENAI_API_KEY"] = api_key_input
            os.environ["OPENAI_API_KEY"] = api_key_input
            st.success("APIキーを反映しました")

        st.divider()
        st.subheader("📁 データ読み込み")
        
        # データファイルの自動選択（vendors.json優先）
        data_dir = ROOT / "data"
        
        def resolve_default_path() -> Path:
            """vendors.json → 旧名 → 他の .json → .md の優先順で選択"""
            candidates = [
                data_dir / "vendors.json",
                data_dir / "ベンダー調査JSON練習版.json",
                data_dir / "ベンダー調査.json",
            ]
            for c in candidates:
                if c.exists():
                    return c
            j = sorted(data_dir.glob("*.json"))
            if j:
                return j[0]
            m = sorted(list(data_dir.glob("*.md")) + list(data_dir.glob("*.markdown")))
            if m:
                return m[0]
            return data_dir
        
        try:
            auto_file = resolve_default_path()
            default_input = str(auto_file)
            st.caption(f"自動選択: {auto_file.name}")
        except Exception:
            default_input = str(data_dir / "vendors.json")
            st.caption("データファイルが見つかりません")
        
        input_path = st.text_input("入力パス（.json/.md または ディレクトリ）", value=default_input)
        
        # JSONの場合はchunk_size=0固定
        is_json = input_path.lower().endswith('.json')
        if is_json:
            st.caption("JSON形式: chunk_size=0固定（1ベンダー=1ドキュメント）")
            effective_chunk_size = 0
        else:
            effective_chunk_size = chunk_size
        
        load_data = st.button("📥 データ読み込み / 再インデックス", use_container_width=True)

        top_k = st.slider("Top K（取得文書数）", 1, 15, config.DEFAULT_TOP_K)
        chunk_size = st.number_input(
            "チャンクサイズ",
            min_value=0,
            max_value=2000,
            value=config.CHUNK_SIZE,
            step=50,
            help="0 を指定すると文字数チャンク分割を無効化（ベンダー単位のみ）"
        )
        chunk_overlap = st.number_input(
            "チャンクオーバーラップ",
            min_value=0,
            max_value=500,
            value=config.CHUNK_OVERLAP,
            step=20,
            help="文字数チャンクを使う場合のみ有効（chunk_size>0）。"
        )
        use_mmr = st.checkbox("MMRを使う（多様性）", value=config.USE_MMR)
        st.caption("※ MMRは類似しすぎる候補を減らして多様化します")
        score_threshold = st.number_input("スコアしきい値（0.0～1.0 / 空欄で未使用）", min_value=0.0, max_value=1.0, value=0.0, step=0.05)
        threshold = None if score_threshold == 0.0 else score_threshold

        st.divider()
        embed_model = st.selectbox("Embeddings", ["text-embedding-3-small", "text-embedding-3-large"], index=0)
        chat_model = st.selectbox("Chat Model", ["gpt-3.5-turbo", "gpt-4o-mini"], index=0)
        temperature = st.slider("Temperature", 0.0, 1.0, config.TEMPERATURE, 0.1)

        reindex = st.button("🔄 インデックス再作成（ベクトルストア消去）")

        st.divider()
        st.caption("FAISS 保存先（ASCIIパス推奨）")
        vector_dir_input = st.text_input(
            "Vectorstore Directory",
            value=str(config.VECTOR_DIR),
            help="日本語など非ASCIIを含まないパスを指定してください（例: C:\\vendor0922\\vectorstore）"
        )
        
        # ASCIIバリデーション
        def _is_ascii(s: str) -> bool:
            try:
                s.encode("ascii")
                return True
            except UnicodeEncodeError:
                return False

        if vector_dir_input and not _is_ascii(vector_dir_input):
            st.error("保存先に日本語など非ASCII文字が含まれています。ASCIIのみのパスを指定してください。")
            st.stop()

        # バリデーション通過後に作成
        if vector_dir_input:
            os.makedirs(vector_dir_input, exist_ok=True)
        st.caption(f"Vectorstore Dir (effective): {vector_dir_input}")

    # 再作成ならvectorstore削除
    if reindex and vector_dir_input:
        shutil.rmtree(vector_dir_input, ignore_errors=True)
        os.makedirs(vector_dir_input, exist_ok=True)
        st.toast("既存ベクトルストアを削除しました。次回検索時に再作成します。", icon="🗑️")

    # データ読み込み（新しいロジック）
    if load_data or "docs" not in st.session_state:
        # 読み込み前にセッションをリセット
        if load_data:
            for k in ("docs", "vs"):
                if k in st.session_state:
                    del st.session_state[k]
        
        try:
            input_path_obj = Path(input_path)
            
            # フォールバック機能：指定パスが存在しない場合
            if not input_path_obj.exists():
                fallback = resolve_default_path()
                st.info(f"指定パスが見つかりませんでした。フォールバックします: {fallback}")
                input_path_obj = fallback
            
            if input_path_obj.is_dir():
                docs = load_documents_from_dir(input_path_obj, chunk_size=effective_chunk_size, chunk_overlap=chunk_overlap)
                st.success(f"📁 ディレクトリ読み込み完了: {input_path_obj}（{len(docs)} ドキュメント）")
            else:
                docs = load_documents_auto(input_path_obj, chunk_size=effective_chunk_size, chunk_overlap=chunk_overlap)
                st.success(f"📄 ファイル読み込み完了: {input_path_obj.name}（{len(docs)} ドキュメント）")
            
            st.session_state["docs"] = docs
            st.session_state["loaded_file"] = str(input_path_obj)
            
        except Exception as e:
            st.error(f"データ読み込みエラー: {e}")
            st.info("💡 data/ に vendors.json か .md ファイルを置いてください")
            st.stop()
    else:
        docs = st.session_state.get("docs", [])
        loaded_file = st.session_state.get("loaded_file", "不明")
        st.caption(f"📄 読み込み済み: {Path(loaded_file).name}（{len(docs)} ドキュメント）")

    # Embeddings / LLM 準備の直前にキーチェック
    api_key = resolve_openai_key()
    st.caption("KEY head: " + (api_key[:10] if api_key else ""))  # 確認表示

    if not api_key:
        st.error("OpenAI APIキーが未設定です。左のサイドバーに入力してください。")
        st.stop()

    # 以降、明示的にキーを渡す
    embeddings = get_embeddings(embed_model, api_key=api_key)
    llm = get_chat(chat_model, temperature=temperature, api_key=api_key)

    # ベクトルストア用意
    try:
        vectorstore, created, used_dir = build_or_load_vectorstore(
            docs=docs,
            embeddings=embeddings,
            persist_dir=vector_dir_input,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            splitter_fn=make_splits,
        )
        st.info("ベクトルストア: 新規作成" if created else "ベクトルストア: 既存を使用")
        st.caption(f"実際の保存先: {used_dir}")
        
        # ユーザー指定と実際の保存先が違う → フォールバックした合図
        if used_dir and vector_dir_input and used_dir.strip().lower() != vector_dir_input.strip().lower():
            st.warning("指定パスに保存できなかったため、フォールバック先を使用しています。")
    except ValueError as e:
        st.error(str(e))
        st.stop()
    

    # プロンプト
    prompt_text = read_prompt_file(config.PROMPT_PATH)
    prompt = load_prompt(prompt_text)

    # タブUI
    tab1, tab2, tab3 = st.tabs(["🔎 検索UI", "📚 KBビューア", "📊 ブラウズ"])
    
    with tab1:
        # 入力UI
        st.subheader("質問を入力")
        q = st.text_input("例: 法務カテゴリで価格帯が低いベンダーを教えて", key="query")
        go = st.button("検索", type="primary")

        if go or q:
            with st.spinner("検索中..."):
                try:
                    chain = make_chain(
                        vectorstore=vectorstore,
                        llm=llm,
                        top_k=top_k,
                        prompt=prompt,
                        use_mmr=use_mmr,
                        score_threshold=threshold
                    )
                    result = chain({"query": q})

                    st.subheader("📝 回答")
                    st.write(result["result"])

                    if result.get("source_documents"):
                        with st.expander("📚 参照ソース抜粋（上位3件）", expanded=False):
                            for i, doc in enumerate(result["source_documents"][:3]):
                                st.markdown(f"**ソース {i+1}** - `{doc.metadata.get('file_path')}`")
                                txt = doc.page_content
                                st.text(txt[:800] + ("..." if len(txt) > 800 else ""))
                                st.caption(str(doc.metadata))

                except Exception as e:
                    st.error(f"検索エラー: {e}")
    
    with tab2:
        st.subheader("📚 ナレッジベースビューア")
        
        if not docs:
            st.info("データが読み込まれていません。左のサイドバーから「データ読み込み」を実行してください。")
        else:
            # サマリ情報の計算
            from collections import Counter, defaultdict
            
            total_vendors = len(docs)
            
            # ステータス別件数
            status_counts = Counter([d.metadata.get("status", "不明") for d in docs])
            category_counts = Counter([d.metadata.get("category", "不明") for d in docs])
            source_format_counts = Counter([d.metadata.get("source_format", "不明") for d in docs])
            
            # メタデータ欠損チェック
            missing = defaultdict(list)
            for i, d in enumerate(docs):
                for key in ("vendor_id", "name", "category", "status"):
                    if not d.metadata.get(key):
                        missing[key].append(i)
            
            # サマリ表示
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("総ベンダー数", total_vendors)
            
            with col2:
                st.metric("vendor_id欠落", len(missing.get("vendor_id", [])))
            
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
            
            # メタデータ欠損表示
            if missing:
                st.warning("メタデータ欠損: " + ", ".join([f"{k}={len(v)}件" for k,v in missing.items()]))
            else:
                st.info("メタデータ欠損なし")
            
            # ドキュメント一覧
            st.subheader("📋 ドキュメント一覧")
            
            for i, doc in enumerate(docs[:50]):  # 表示上限
                meta = doc.metadata
                
                with st.expander(f"#{i+1} {meta.get('vendor_id', 'No ID')} — {meta.get('name', 'Unknown')}", expanded=False):
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
                        if vendor_id and vectorstore:
                            if st.button(f"🔍 {vendor_id} で検索", key=f"search_{i}"):
                                st.session_state[f"search_query_{i}"] = vendor_id
                        
                        # 検索結果表示
                        if f"search_query_{i}" in st.session_state and vectorstore:
                            query = st.session_state[f"search_query_{i}"]
                            try:
                                search_results = vectorstore.similarity_search(query, k=3)
                                st.markdown(f"**「{query}」の検索結果:**")
                                for j, result in enumerate(search_results):
                                    with st.expander(f"結果 {j+1}", expanded=False):
                                        st.text(result.page_content[:300] + ("..." if len(result.page_content) > 300 else ""))
                            except Exception as e:
                                st.error(f"検索エラー: {e}")
    
    with tab3:
        # ブラウズタブ
        docs = st.session_state.get("docs", [])
        browse_tab(docs)

if __name__ == "__main__":
    main()
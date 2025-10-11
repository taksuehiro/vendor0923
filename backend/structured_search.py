# backend/structured_search.py
"""
構造化検索モジュール
vendors.jsonをPandas DataFrameとして管理し、メタデータベースのフィルタリングを提供
"""
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS

from backend.vectorstore import BedrockEmbeddingsCompat

log = logging.getLogger(__name__)

# グローバルキャッシュ
_vendors_df: Optional[pd.DataFrame] = None
_embeddings: Optional[BedrockEmbeddingsCompat] = None


def load_vendors_df() -> pd.DataFrame:
    """vendors.jsonをDataFrameとしてロード（シングルトン）"""
    global _vendors_df
    if _vendors_df is not None:
        return _vendors_df
    
    data_path = Path(__file__).parent / "data" / "vendors.json"
    log.info(f"Loading vendors from {data_path}")
    
    with open(data_path, encoding='utf-8') as f:
        data = json.load(f)
    
    # json_normalizeでネスト構造を展開
    _vendors_df = pd.json_normalize(data)
    log.info(f"Loaded {len(_vendors_df)} vendors")
    
    return _vendors_df


def get_embeddings() -> BedrockEmbeddingsCompat:
    """Embeddingsインスタンスを取得（シングルトン）"""
    global _embeddings
    if _embeddings is not None:
        return _embeddings
    
    model_id = os.getenv("BEDROCK_EMBEDDINGS_MODEL_ID", "amazon.titan-embed-text-v1")
    region = os.getenv("AWS_REGION", "ap-northeast-1")
    
    _embeddings = BedrockEmbeddingsCompat(
        model_id=model_id,
        region_name=region
    )
    log.info(f"Initialized embeddings: {model_id}")
    
    return _embeddings


def detect_filters(query: str) -> Dict[str, str]:
    """
    クエリから構造化フィルタを検出
    
    Returns:
        dict: キーがDataFrameのカラム名、値がフィルタ値
    """
    filters = {}
    
    # 面談ステータス
    if re.search(r'面談済(み)?', query):
        filters['engagement.status'] = '面談済'
    elif re.search(r'未面談', query):
        filters['engagement.status'] = '未面談'
    
    # 上場区分
    if re.search(r'上場(?!.*未)', query):  # 「未上場」でないことを確認
        filters['corporate.listed'] = '上場'
    elif re.search(r'未上場', query):
        filters['corporate.listed'] = '未上場'
    
    # ベンダータイプ
    if re.search(r'\bSaaS\b', query, re.IGNORECASE):
        filters['type'] = 'SaaS'
    elif re.search(r'スクラッチ', query):
        filters['type'] = 'スクラッチ'
    elif re.search(r'\bSI\b', query):
        filters['type'] = 'SI'
    
    log.info(f"Detected filters: {filters}")
    return filters


def extract_semantic_part(query: str) -> str:
    """
    クエリから構造化キーワードを除去してセマンティック部分を抽出
    
    例: "面談済みのチャットボット企業" → "チャットボット企業"
    """
    semantic = query
    
    # 構造化キーワードを削除
    keywords_to_remove = [
        '面談済み', '面談済', 
        '未面談',
        '上場', '未上場',
        'SaaS', 'スクラッチ', 'SI',
        'の', 'を', '教えて', '見せて', 'ください'
    ]
    
    for keyword in keywords_to_remove:
        semantic = re.sub(keyword, '', semantic, flags=re.IGNORECASE)
    
    semantic = semantic.strip()
    log.info(f"Extracted semantic part: '{semantic}' from '{query}'")
    
    return semantic


def apply_filters(df: pd.DataFrame, filters: Dict[str, str]) -> pd.DataFrame:
    """DataFrameにフィルタを適用"""
    filtered = df.copy()
    
    for column, value in filters.items():
        if column in filtered.columns:
            filtered = filtered[filtered[column] == value]
            log.info(f"Applied filter {column}={value}, remaining: {len(filtered)}")
        else:
            log.warning(f"Column {column} not found in DataFrame")
    
    return filtered


def structured_search(filters: Dict[str, str], k: int = 10) -> List[Dict]:
    """
    純粋な構造化検索（ベクトル検索なし）
    
    Returns:
        list: 検索結果（score=1.0固定）
    """
    df = load_vendors_df()
    filtered = apply_filters(df, filters)
    
    results = []
    for _, row in filtered.head(k).iterrows():
        results.append({
            "page_content": row.get('name', ''),
            "similarity": 1.0,  # 完全一致として100%
            "metadata": row.to_dict()
        })
    
    log.info(f"Structured search returned {len(results)} results")
    return results


def hybrid_search(
    filters: Dict[str, str], 
    semantic_query: str, 
    k: int = 5
) -> List[Dict]:
    """
    ハイブリッド検索（構造化フィルタ + セマンティック検索）
    
    Args:
        filters: Pandasフィルタ条件
        semantic_query: セマンティック検索クエリ
        k: 返す結果数
    
    Returns:
        list: 検索結果（similarity付き）
    """
    df = load_vendors_df()
    
    # Step 1: Pandasフィルタ
    filtered = apply_filters(df, filters)
    
    if len(filtered) == 0:
        log.info("No results after filtering")
        return []
    
    log.info(f"Filtered to {len(filtered)} vendors, performing semantic search")
    
    # Step 2: フィルタ結果をDocumentに変換
    docs = []
    for _, row in filtered.iterrows():
        # テキスト生成（name + description）
        text_parts = [row.get('name', '')]
        
        if 'offerings.description_short' in row:
            desc = row.get('offerings.description_short', '')
            if desc:
                text_parts.append(desc)
        
        text = '\n'.join(text_parts)
        
        docs.append(Document(
            page_content=text,
            metadata=row.to_dict()
        ))
    
    # Step 3: 一時的なFAISSインデックス作成
    embeddings = get_embeddings()
    temp_vs = FAISS.from_documents(docs, embeddings)
    log.info(f"Created temporary FAISS index with {len(docs)} documents")
    
    # Step 4: セマンティック検索
    faiss_results = temp_vs.similarity_search_with_score(semantic_query, k=k)
    
    # Step 5: 結果を整形
    results = []
    for doc, distance in faiss_results:
        # 距離を類似度に変換
        similarity = float(1.0 / (1.0 + distance))
        results.append({
            "page_content": doc.page_content,
            "similarity": similarity,
            "metadata": doc.metadata
        })
    
    log.info(f"Hybrid search returned {len(results)} results")
    return results


def classify_query(query: str, use_llm: bool = False) -> Tuple[str, Dict[str, str], str]:
    """
    クエリを分類して検索タイプを決定
    
    Args:
        query: ユーザークエリ
        use_llm: LLMベースの分類を使用するか（デフォルト：False）
    
    Returns:
        tuple: (search_type, filters, semantic_query)
            search_type: "structured" | "hybrid" | "semantic"
            filters: 構造化フィルタ
            semantic_query: セマンティック検索クエリ
    """
    # LLMベースの分類（オプション）
    if use_llm:
        try:
            from backend.bedrock_llm import classify_query_with_llm
            result = classify_query_with_llm(query)
            
            if result:
                return (
                    result.get("type", "semantic"),
                    result.get("filters", {}),
                    result.get("semantic_query", query)
                )
        except Exception as e:
            log.warning(f"LLM classification failed, using rule-based: {e}")
    
    # ルールベースの分類（デフォルト）
    filters = detect_filters(query)
    semantic_part = extract_semantic_part(query)
    
    if filters and not semantic_part:
        return ("structured", filters, "")
    elif filters and semantic_part:
        return ("hybrid", filters, semantic_part)
    else:
        return ("semantic", {}, query)


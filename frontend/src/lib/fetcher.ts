// src/lib/fetcher.ts
export async function fetchJson<T>(
  input: RequestInfo | URL,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(input, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
  }
  // 型安全: 実体はランタイムで保証できないので T へアサート
  return (await res.json()) as T;
}

// 検索API呼び出しの共通関数
export interface SearchRequest {
  query: string;
  top_k: number;
  mmr?: number;
}

export interface SearchResult {
  id: string;
  title: string;
  score: number;
  snippet: string;
  metadata: {
    status: string;
    category: string;
  };
}

export interface SearchResponse {
  hits: SearchResult[];
}

export async function searchVendors(request: SearchRequest): Promise<SearchResponse> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8080';
  
  try {
    const response = await fetch(`${baseUrl}/search`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "omit",
      body: JSON.stringify(request),
    });
    
    // レスポンスの存在確認
    if (!response) {
      throw new Error('レスポンスが取得できませんでした');
    }
    
    // HTTPステータスコードの確認
    if (!response.ok) {
      const errorText = await response.text().catch(() => '');
      throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
    }
    
    const json = await response.json();
    
    // 防御的パース: json.hits または json.data.hits のどちらでも動く
    const hits = Array.isArray(json?.hits)
      ? json.hits
      : Array.isArray(json?.data?.hits)
        ? json.data.hits
        : [];
    
    // 最終的な配列の検証
    if (!Array.isArray(hits)) {
      throw new Error("Unexpected response shape");
    }
    
    return { hits };
  } catch (error) {
    console.error("Search API error:", error);
    throw new Error(`検索API呼び出しに失敗しました: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

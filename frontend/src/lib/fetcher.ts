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

export interface SearchHit {
  id: string;
  title: string;
  score: number;
  snippet: string;
  metadata: Record<string, unknown>;
}

export interface SearchResponse {
  hits: SearchHit[];
}

export async function searchVendors(request: SearchRequest): Promise<SearchResponse> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
  
  try {
    const response = await fetchJson<SearchResponse>(`${baseUrl}/search`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });
    
    return response;
  } catch (error) {
    console.error("Search API error:", error);
    throw new Error(`検索API呼び出しに失敗しました: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

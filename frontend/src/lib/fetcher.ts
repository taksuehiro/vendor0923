// frontend/src/lib/fetcher.ts
import { apiBase } from "./apiBase";
import { normalizeSearchResults, type ViewResult } from "./scoreNormalizer";

export type SearchHit = {
  id: string;
  title: string;
  score?: number;
  scorePct?: number;
  snippet?: string;
  // 必要なら他のフィールドも追加
};

export type SearchResponse = {
  status: "ok" | "error";
  hits: SearchHit[];
  raw: any; // デバッグ用に素のレスポンスも返す
};

export async function searchApi(
  body: Record<string, any>,
  base = apiBase
): Promise<SearchResponse> {
  const res = await fetch(`${base}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "omit", // CORSの想定と一致させる
    body: JSON.stringify(body),
  });

  // JSON化に失敗してもUIが死なないようにフォールバック
  const json = await res.json().catch(() => ({} as any));

  const status: "ok" | "error" =
    (json?.metadata?.status as any) ?? (res.ok ? "ok" : "error");

  const rawHits = Array.isArray(json?.hits) ? json.hits : [];
  const normalizedHits = normalizeSearchResults(rawHits);

  // ViewResultをSearchHitに変換
  const searchHits: SearchHit[] = normalizedHits.map(hit => ({
    id: hit.id || '',
    title: hit.title || '',
    score: hit.score,
    scorePct: hit.scorePct,
    snippet: hit.snippet || '',
    url: hit.url,
    status: hit.status
  }));

  return { status, hits: searchHits, raw: json };
}

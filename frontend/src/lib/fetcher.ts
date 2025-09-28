// frontend/src/lib/fetcher.ts
export type SearchHit = {
  id: string;
  title: string;
  score?: number;
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
  base = process.env.NEXT_PUBLIC_API_BASE!
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

  const hits: SearchHit[] = Array.isArray(json?.hits) ? json.hits : [];

  return { status, hits, raw: json };
}

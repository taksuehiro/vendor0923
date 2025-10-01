import type { SearchResponse, SearchHit, ResponseMetadata } from "@/types";

type SearchBody = { query: string; k?: number; use_mmr?: boolean };

export async function searchApi(body: SearchBody): Promise<SearchResponse> {
  const base = process.env.NEXT_PUBLIC_API_BASE!;
  const res = await fetch(`${base}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "omit",
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${res.status} ${res.statusText}: ${text.slice(0,200)}`);
  }

  const json = (await res.json()) as unknown;
  const root = (json ?? {}) as Record<string, unknown>;
  const data = (root.data ?? {}) as Record<string, unknown>;

  const rawHits =
    Array.isArray(root.hits)
      ? (root.hits as unknown[])
      : Array.isArray(data.hits as unknown[])
      ? ((data.hits as unknown[]))
      : [];

  const hits: SearchHit[] = rawHits.map((h) => {
    const r = (h ?? {}) as Record<string, unknown>;
    return {
      id: String(r.id ?? ""),
      title: String(r.title ?? ""),
      score: typeof r.score === "number" ? r.score : 0,
      snippet: typeof r.snippet === "string" ? r.snippet : "",
      url: typeof r.url === "string" ? r.url : undefined,
      status: typeof r.status === "string" ? r.status : undefined,
    };
  });

  const metadata = (root.metadata ?? data.metadata) as ResponseMetadata | undefined;
  return { hits, metadata };
}
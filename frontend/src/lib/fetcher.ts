import type { SearchResponse, SearchHit, Metadata } from "@/types";

export async function searchApi(q: string): Promise<SearchResponse> {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "omit",
    body: JSON.stringify({ query: q, k: 10, use_mmr: false }),
  });

  // HTTPはOKでも中身が壊れてる可能性に備える
  let json: any = null;
  try {
    json = await res.json();
  } catch {
    return { hits: [], metadata: { source: "parse_error" } };
  }

  const hits: SearchHit[] = json?.hits ?? json?.data?.hits ?? [];
  const metadata: Metadata | undefined = json?.metadata ?? json?.data?.metadata ?? undefined;

  return { hits, metadata };
}
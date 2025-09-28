import { SearchResponse } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE!;
if (!API_BASE) {
  // 早期に気付けるように
  // eslint-disable-next-line no-console
  console.warn("NEXT_PUBLIC_API_BASE is not set");
}

async function parseJson<T>(res: Response): Promise<T> {
  const text = await res.text();
  try {
    return JSON.parse(text) as T;
  } catch {
    throw new Error(`Invalid JSON response: ${text.slice(0, 200)}`);
  }
}

export async function searchApi(payload: {
  query: string;
  k?: number;
  use_mmr?: boolean;
}): Promise<SearchResponse> {
  const url = `${API_BASE.replace(/\/$/, "")}/search`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    // CORSでCookieを使わない前提
    credentials: "omit",
  });

  // 200系以外は本文メッセージを拾って投げ直す
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body || res.statusText}`);
  }

  // モック/本番 両対応
  const json = await parseJson<unknown>(res);

  const hits =
    (json as any)?.hits ??
    (json as any)?.data?.hits ??
    [];

  const metadata =
    (json as any)?.metadata ??
    (json as any)?.data?.metadata ??
    undefined;

  if (!Array.isArray(hits)) {
    throw new Error("Response format error: hits is not an array");
  }

  return { hits, metadata } as SearchResponse;
}
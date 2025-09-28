export async function getJson<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const res = await fetch(input, {
    credentials: "omit",
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  // Always try JSON; if fails, throw with body text
  const text = await res.text();
  let json: unknown;
  try {
    json = text ? JSON.parse(text) : {};
  } catch {
    throw new Error(`Invalid JSON: ${text?.slice(0, 200)}`);
  }
  if (!res.ok) {
    throw new Error(`HTTP ${res.status} ${res.statusText}: ${text?.slice(0, 200)}`);
  }
  return json as T;
}

import type { ApiResponse, SearchHit } from "@/lib/types";

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";

export async function searchApi(query: string, k = 3, use_mmr = false) {
  const body = JSON.stringify({ query, k, use_mmr });
  const r = await getJson<ApiResponse<SearchHit>>(`${BASE}/search`, {
    method: "POST",
    body,
  });
  // Defensive parse: accept {hits} or {data:{hits}}
  const hits = (r.hits ?? r.data?.hits) ?? [];
  const meta = r.metadata;
  return { hits, meta };
}
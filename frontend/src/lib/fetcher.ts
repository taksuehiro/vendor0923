import type { SearchResponse } from "./types";

export async function postJSON<T = unknown>(url: string, body: unknown, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "omit",
    body: JSON.stringify(body ?? {}),
    ...init,
  });
  // 2xx 以外は例外
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}: ${text || res.statusText}`);
  }
  const json = (await res.json().catch(() => ({}))) as unknown;
  // defensive parse
  const obj = typeof json === "object" && json ? (json as Record<string, unknown>) : {};
  const data = (obj["data"] ?? obj) as Record<string, unknown>;
  return data as T;
}

export async function searchApi(
  base: string,
  payload: { query: string; k?: number; use_mmr?: boolean }
) {
  const url = `${base.replace(/\/$/, "")}/search`;
  const data = await postJSON<SearchResponse>(url, payload);
  const hits = Array.isArray(data?.hits) ? data.hits : [];
  return { hits, meta: data?.metadata, raw: data };
}
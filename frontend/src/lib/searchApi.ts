// frontend/src/lib/searchApi.ts
import { apiBase } from "./apiBase";
import { normalizeSearchResults } from "./scoreNormalizer";

export async function searchVendors(query: string) {
  const res = await fetch(`${apiBase}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Search failed: ${res.status} ${text}`);
  }
  const data = await res.json(); // { results: [...] }
  
  // APIレスポンスをコンソールに出力
  console.log("API Response:", data);
  
  const normalizedResults = normalizeSearchResults(data.results || []);
  return { ...data, results: normalizedResults };
}

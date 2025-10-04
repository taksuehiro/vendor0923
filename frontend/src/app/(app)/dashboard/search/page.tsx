"use client";
import { useState } from "react";
import { apiBase } from "@/lib/apiBase";
import { normalizeSearchResults, type ViewResult } from "@/lib/scoreNormalizer";

type Hit = {
  id?: string;
  title?: string;
  snippet?: string;
  score?: number;
  scorePct?: number;
  url?: string;
  [k: string]: any;
};

export default function SearchPage() {
  const [q, setQ] = useState("");
  const [k, setK] = useState(8);
  const [useMmr, setUseMmr] = useState(true);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [hits, setHits] = useState<ViewResult[]>([]);
  const [raw, setRaw] = useState<any>(null);

  const onSearch = async () => {
    setErr(null);
    setLoading(true);
    setHits([]);
    try {
      const res = await fetch(`${apiBase}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, k, use_mmr: useMmr }),
      });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(`API ${res.status}: ${text || res.statusText}`);
      }
      const json = await res.json();
      
      // APIレスポンスをコンソールに出力
      console.log("API Response:", json);
      
      // いくつかの形に耐える防御的マッピング
      const rawResults =
        json?.hits ??
        json?.results ??
        (Array.isArray(json) ? json : []) ??
        [];
      const normalizedResults = normalizeSearchResults(rawResults);
      setHits(normalizedResults);
      setRaw(json);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Knowledge Search</h1>
      </header>

      <section className="rounded-xl border p-4 space-y-3">
        <div className="flex gap-3">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="検索語を入力"
            className="w-full border rounded-md px-3 py-2"
          />
          <button
            onClick={onSearch}
            disabled={loading || !q.trim()}
            className="border rounded-md px-4 py-2 disabled:opacity-50"
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </div>
        <div className="flex gap-4 text-sm items-center">
          <label className="flex items-center gap-2">
            <span>K:</span>
            <input
              type="number"
              min={1}
              max={50}
              value={k}
              onChange={(e) => setK(Number(e.target.value))}
              className="w-20 border rounded px-2 py-1"
            />
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={useMmr}
              onChange={(e) => setUseMmr(e.target.checked)}
            />
            <span>MMR を使う</span>
          </label>
        </div>
        {err && <p className="text-red-600 text-sm">Error: {err}</p>}
      </section>

      <section className="space-y-3">
        {loading && (
          <div className="animate-pulse">
            <div className="h-5 w-48 bg-gray-200 rounded mb-2" />
            <div className="h-24 bg-gray-100 rounded" />
          </div>
        )}

        {!loading && hits.length > 0 && (
          <ul className="grid gap-3">
            {hits.map((h, i) => (
              <li key={h.id ?? i} className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium">
                    {h.title ?? h.metadata?.title ?? `Doc #${i + 1}`}
                  </h3>
                  {typeof h.scorePct === "number" && (
                    <span className="text-xs opacity-70">
                      score: {Number(h.scorePct).toFixed(1)}%
                    </span>
                  )}
                </div>
                <p className="text-sm mt-2 line-clamp-3">
                  {h.snippet ?? h.page_content ?? h.metadata?.summary ?? ""}
                </p>
                {(h.url || h.metadata?.url) && (
                  <a
                    className="text-sm text-blue-600 hover:underline mt-2 inline-block"
                    href={h.url ?? h.metadata?.url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    ソースを開く
                  </a>
                )}
              </li>
            ))}
          </ul>
        )}

        {!loading && !err && hits.length === 0 && (
          <p className="text-sm opacity-70">検索結果がここに表示されます。</p>
        )}

        {/* デバッグ用：必要なら消してください */}
        {raw && (
          <details className="mt-4">
            <summary className="cursor-pointer text-sm">Raw response</summary>
            <pre className="text-xs bg-gray-50 p-3 rounded overflow-auto">
              {JSON.stringify(raw, null, 2)}
            </pre>
          </details>
        )}
      </section>
    </div>
  );
}

"use client";
import { useState } from "react";
import { ViewResult } from "@/types";

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
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE;
      console.log("API_BASE", API_BASE);

      const payload = {
        query: q,
        k: k,
        use_mmr: useMmr,
      };
      console.log("POST /search payload", payload);

      const res = await fetch(`${API_BASE}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(`API ${res.status}: ${text || res.statusText}`);
      }
      
      const json = await res.json();
      console.log("POST /search response", json);
      
      // 安全ガード
      const results: Array<{ text: string; score: number; metadata?: any }> =
        Array.isArray(json?.results) ? json.results : [];

      if (!results.length) {
        setHits([]);
        setRaw(json);
        return;
      }

      // コサイン類似度を直接パーセンテージ変換（APIレスポンスはすでに0〜1の類似度）
      const enriched = results.map((r, idx) => {
        const scorePct = Math.round(Number(r.score) * 1000) / 10;  // 例: 0.496 → 49.6%
        return {
          id: idx + 1,
          text: r.text,
          metadata: r.metadata ?? {},
          rawScore: r.score,
          scorePct,
        };
      });

      // 関連度の高い順に並べ替え
      enriched.sort((a, b) => b.scorePct - a.scorePct);

      setHits(enriched);
      setRaw(json);
    } catch (e: any) {
      console.error("search error", e);
      setErr(e?.message ?? String(e));
      setHits([]);
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
                    Doc #{h.id}
                  </h3>
                  {typeof h.scorePct === "number" && (
                    <span className="text-xs opacity-70">
                      score: {h.scorePct.toFixed(1)}%
                    </span>
                  )}
                </div>
                <p className="text-sm mt-2 line-clamp-3">
                  {h.text}
                </p>
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

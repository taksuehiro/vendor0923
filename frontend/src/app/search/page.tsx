"use client";
import { useState } from "react";
import type { SearchHit, Metadata } from "@/lib/types";
import { searchApi } from "@/lib/fetcher";

export default function SearchPage() {
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [meta, setMeta] = useState<Metadata | undefined>(undefined);
  const [q, setQ] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function onSearch() {
    setError(null);
    try {
      const base = process.env.NEXT_PUBLIC_API_BASE ?? "";
      const res = await searchApi(base, { query: q, k: 3, use_mmr: false });
      setHits(res.hits);
      setMeta(res.meta);
    } catch (e) {
      setHits([]);
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  return (
    <main className="p-4 space-y-4">
      <h1 className="text-xl font-bold">検索UI</h1>
      <input
        className="border rounded px-2 py-1 w-full max-w-xl"
        placeholder="検索クエリ"
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />
      <button className="px-3 py-1 rounded bg-black text-white" onClick={onSearch}>
        検索
      </button>
      {meta?.provider && (
        <div className="text-xs opacity-60">provider: {meta.provider}</div>
      )}
      {error && (
        <div className="text-red-600 text-sm">検索中にエラーが発生しました: {error}</div>
      )}
      <ol className="space-y-2 list-decimal pl-6">
        {hits.map((h) => (
          <li key={h.id}>
            <b>{h.title}</b>（スコア: {h.score}）<div className="opacity-70">{h.snippet}</div>
          </li>
        ))}
      </ol>
    </main>
  );
}
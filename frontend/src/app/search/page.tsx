"use client";
import { useState } from "react";
import { searchApi } from "@/lib/fetcher";
import type { SearchHit } from "@/types";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [meta, setMeta] = useState<any | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>("");

  const onSearch = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await searchApi({ query });
      setHits(res.hits);
      // metadata は存在しないため削除
      setMeta(undefined);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="p-4 space-y-4">
      <h1 className="text-xl font-bold">検索UI</h1>
      <input
        className="border rounded px-2 py-1 w-full max-w-xl"
        placeholder="検索クエリ"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button 
        className="px-3 py-1 rounded bg-black text-white disabled:opacity-50" 
        onClick={onSearch}
        disabled={loading}
      >
        {loading ? "検索中…" : "検索"}
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
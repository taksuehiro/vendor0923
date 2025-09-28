"use client";

import { useState } from "react";
import { searchApi, type SearchHit } from "@/lib/fetcher";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSearch = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const { status, hits } = await searchApi({ query, k: 3, use_mmr: false });
      if (status !== "ok") {
        setErrorMsg("検索中にエラーが発生しました（status=error）");
        setHits([]);
      } else {
        setHits(hits);
      }
    } catch (e: any) {
      setErrorMsg(e?.message ?? "検索中に例外が発生しました");
      setHits([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 space-y-4">
      <div className="flex gap-2">
        <input
          className="border rounded px-3 py-2 flex-1"
          placeholder="検索クエリ"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button
          className="px-4 py-2 rounded bg-black text-white disabled:opacity-50"
          onClick={onSearch}
          disabled={loading}
        >
          {loading ? "検索中..." : "検索"}
        </button>
      </div>

      {errorMsg && (
        <div className="p-3 rounded border border-red-300 text-red-700 bg-red-50">
          {errorMsg}
        </div>
      )}

      <div className="space-y-2">
        {hits.map((h) => (
          <div key={h.id} className="p-3 rounded border">
            <div className="font-medium">{h.title}</div>
            {h.snippet && <div className="text-sm text-gray-600">{h.snippet}</div>}
          </div>
        ))}
        {!errorMsg && !loading && hits.length === 0 && (
          <div className="text-gray-500 text-sm">結果はありません</div>
        )}
      </div>
    </div>
  );
}
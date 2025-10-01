"use client";
import { useState } from "react";
import { searchVendors } from "@/lib/searchApi";

export default function Page() {
  const [q, setQ] = useState("");
  const [data, setData] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  const onSearch = async () => {
    setErr(null);
    try {
      const json = await searchVendors(q);
      setData(json);
    } catch (e: any) {
      setErr(e.message);
    }
  };

  return (
    <main className="p-6">
      <div className="flex gap-2">
        <input 
          value={q} 
          onChange={e=>setQ(e.target.value)} 
          placeholder="検索語" 
          className="border px-2 py-1" 
        />
        <button 
          onClick={onSearch} 
          className="border px-3 py-1"
        >
          Search
        </button>
      </div>
      {err && <p className="text-red-600 mt-3">{err}</p>}
      {data && <pre className="mt-3">{JSON.stringify(data, null, 2)}</pre>}
    </main>
  );
}
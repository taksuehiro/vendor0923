"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { searchVendors, type SearchResult } from "@/lib/fetcher";

// SearchResult型は既にfetcher.tsで定義済み

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [topK, setTopK] = useState(5);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      const response = await searchVendors({
        query,
        top_k: topK,
        mmr: 0.5,
      });

      setResults(response.hits);
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      console.error("Search error:", error);
      // エラー時のフォールバック
      setResults([]);
      // エラーメッセージを表示（UIに追加する場合はここで状態管理）
      alert(`検索中にエラー: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            🔍 ベンダー検索
          </h1>
          <p className="text-gray-600">
            自然言語でベンダー情報を検索できます
          </p>
        </div>

        <Card className="mb-8">
          <CardHeader>
            <CardTitle>検索条件</CardTitle>
            <CardDescription>
              質問形式でベンダーを検索してください
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="query">検索クエリ</Label>
              <Input
                id="query"
                placeholder="例: 契約書管理が得意な会社は？"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSearch()}
              />
            </div>
            <div>
              <Label htmlFor="topK">取得件数</Label>
              <Input
                id="topK"
                type="number"
                min="1"
                max="20"
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value))}
              />
            </div>
            <Button 
              onClick={handleSearch} 
              disabled={loading || !query.trim()}
              className="w-full"
            >
              {loading ? "検索中..." : "検索実行"}
            </Button>
          </CardContent>
        </Card>

        {results.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-2xl font-semibold text-gray-900">
              検索結果 ({results.length}件)
            </h2>
            {results.map((result, index) => (
              <Card key={result.id}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg">
                        #{index + 1} {result.title}
                      </CardTitle>
                      <CardDescription>
                        スコア: {(result.score * 100).toFixed(1)}%
                      </CardDescription>
                    </div>
                    <div className="text-right text-sm">
                      <div className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        {result.metadata.status}
                      </div>
                      <div className="bg-green-100 text-green-800 px-2 py-1 rounded mt-1">
                        {result.metadata.category}
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-700">{result.snippet}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

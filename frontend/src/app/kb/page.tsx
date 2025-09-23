"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";

interface KBStats {
  totalVendors: number;
  byStatus: Record<string, number>;
  byCategory: Record<string, number>;
  missingMetadata: Record<string, number>;
}

export default function KBPage() {
  const [stats, setStats] = useState<KBStats>({
    totalVendors: 20,
    byStatus: {
      "面談済": 12,
      "未面談": 8
    },
    byCategory: {
      "スクラッチ": 8,
      "SaaS": 7,
      "SI": 5
    },
    missingMetadata: {
      "vendor_id": 0,
      "name": 0,
      "category": 0,
      "status": 0
    }
  });

  const [testQuery, setTestQuery] = useState("");
  const [testResults, setTestResults] = useState<any[]>([]);
  const [testLoading, setTestLoading] = useState(false);

  const handleTestSearch = async () => {
    if (!testQuery.trim()) return;

    setTestLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: testQuery,
          top_k: 3,
          mmr: 0.5,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setTestResults(data.hits);
      } else {
        console.error("Test search failed");
      }
    } catch (error) {
      console.error("Test search error:", error);
    } finally {
      setTestLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-6xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            📚 ナレッジベース
          </h1>
          <p className="text-gray-600">
            登録済みデータの確認・検索テスト・統計情報
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* 統計情報 */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>データ統計</CardTitle>
                <CardDescription>
                  登録済みベンダーデータの概要
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <div className="text-3xl font-bold text-blue-600">
                    {stats.totalVendors}
                  </div>
                  <div className="text-blue-800">総ベンダー数</div>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">ステータス内訳</h3>
                  <div className="space-y-1">
                    {Object.entries(stats.byStatus).map(([status, count]) => (
                      <div key={status} className="flex justify-between">
                        <span>{status}</span>
                        <span className="font-medium">{count}社</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">カテゴリ上位</h3>
                  <div className="space-y-1">
                    {Object.entries(stats.byCategory).map(([category, count]) => (
                      <div key={category} className="flex justify-between">
                        <span>{category}</span>
                        <span className="font-medium">{count}社</span>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>メタデータ品質</CardTitle>
                <CardDescription>
                  データの完全性チェック
                </CardDescription>
              </CardHeader>
              <CardContent>
                {Object.values(stats.missingMetadata).every(count => count === 0) ? (
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-green-600 font-semibold">
                      ✅ メタデータ欠損なし
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {Object.entries(stats.missingMetadata).map(([field, count]) => (
                      count > 0 && (
                        <div key={field} className="flex justify-between text-orange-600">
                          <span>{field}</span>
                          <span>{count}件</span>
                        </div>
                      )
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* 検索テスト */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>検索テスト</CardTitle>
                <CardDescription>
                  任意のクエリで検索機能をテスト
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="testQuery">テストクエリ</Label>
                  <Input
                    id="testQuery"
                    placeholder="例: 契約書管理、AI、クラウド"
                    value={testQuery}
                    onChange={(e) => setTestQuery(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && handleTestSearch()}
                  />
                </div>
                <Button 
                  onClick={handleTestSearch} 
                  disabled={testLoading || !testQuery.trim()}
                  className="w-full"
                >
                  {testLoading ? "テスト中..." : "テスト実行"}
                </Button>
              </CardContent>
            </Card>

            {testResults.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>テスト結果</CardTitle>
                  <CardDescription>
                    検索結果のプレビュー
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {testResults.map((result, index) => (
                    <div key={result.id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold">
                          #{index + 1} {result.title}
                        </h4>
                        <div className="text-sm text-gray-500">
                          スコア: {(result.score * 100).toFixed(1)}%
                        </div>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">
                        {result.snippet}
                      </p>
                      <div className="flex gap-2">
                        <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                          {result.metadata.status}
                        </span>
                        <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                          {result.metadata.category}
                        </span>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}
          </div>
        </div>

        {/* サンプルデータ */}
        <div className="mt-8">
          <Card>
            <CardHeader>
              <CardTitle>サンプルデータ（先頭5件）</CardTitle>
              <CardDescription>
                登録済みベンダーデータのプレビュー
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  {
                    id: "vendor_1",
                    name: "LiberCraft",
                    category: "スクラッチ",
                    status: "面談済",
                    snippet: "AI・機械学習を活用したスクラッチ開発サービス。契約書管理、法務業務の自動化に強み。"
                  },
                  {
                    id: "vendor_2",
                    name: "TechCorp",
                    category: "SaaS",
                    status: "未面談",
                    snippet: "クラウドインフラ構築・運用支援。AWS、Azure対応。スケーラブルなシステム構築が得意。"
                  },
                  {
                    id: "vendor_3",
                    name: "DataSoft",
                    category: "SI",
                    status: "面談済",
                    snippet: "データ分析・BIツール開発。大規模データ処理、可視化、レポート自動化に強み。"
                  }
                ].map((vendor, index) => (
                  <div key={vendor.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-semibold">
                        #{index + 1} {vendor.name}
                      </h4>
                      <div className="flex gap-2">
                        <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                          {vendor.status}
                        </span>
                        <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                          {vendor.category}
                        </span>
                      </div>
                    </div>
                    <p className="text-sm text-gray-600">
                      {vendor.snippet}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

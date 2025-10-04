"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import type { SearchResult, KBStats, Vendor } from "@/types";

export default function KBPage() {
  const [testQuery, setTestQuery] = useState("");
  const [testResults, setTestResults] = useState<SearchResult[]>([]);
  const [testLoading, setTestLoading] = useState(false);

  const handleTestSearch = async () => {
    if (!testQuery.trim()) return;

    setTestLoading(true);
    try {
      // モック検索結果
      const mockResults: SearchResult[] = [
        {
          id: "vendor_1",
          title: "LiberCraft",
          snippet: "AI・機械学習を活用したスクラッチ開発サービス",
          score: 0.95,
          metadata: {
            status: "interviewed",
            category: "スクラッチ開発"
          }
        },
        {
          id: "vendor_2",
          title: "TechCorp",
          snippet: "クラウドインフラ構築・運用支援",
          score: 0.87,
          metadata: {
            status: "not_interviewed",
            category: "SaaS"
          }
        }
      ];

      setTestResults(mockResults);
    } catch (error) {
      console.error("Test search error:", error);
    } finally {
      setTestLoading(false);
    }
  };

  // モックデータの生成
  const mockStats: KBStats = {
    totalVendors: 20,
    missingCount: 0,
    byFormat: {
      "JSON": 20
    },
    byStatus: {
      interviewed: 12,
      not_interviewed: 8
    },
    topCategories: [
      { name: "スクラッチ", count: 8 },
      { name: "SaaS", count: 7 },
      { name: "SI", count: 5 }
    ]
  };

  const mockVendors: Vendor[] = [
    {
      id: "vendor_1",
      name: "LiberCraft",
      status: "interviewed",
      listed: false,
      type: "スクラッチ",
      category: ["スクラッチ"],
      meta: {
        url: "https://libercraft.com",
        employees_band: "1-10",
        investors: ["投資家A"]
      }
    },
    {
      id: "vendor_2",
      name: "TechCorp",
      status: "not_interviewed",
      listed: true,
      type: "SaaS",
      category: ["SaaS"],
      meta: {
        employees_band: "100-500",
        investors: ["投資家B", "投資家C"]
      }
    },
    {
      id: "vendor_3",
      name: "DataSoft",
      status: "interviewed",
      listed: false,
      type: "SI",
      category: ["SI"],
      meta: {
        employees_band: "50-100",
        investors: ["投資家D"]
      }
    }
  ];

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
                    {mockStats.totalVendors}
                  </div>
                  <div className="text-blue-800">総ベンダー数</div>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">ステータス内訳</h3>
                  <div className="space-y-1">
                    {Object.entries(mockStats.byStatus).map(([status, count]) => (
                      <div key={status} className="flex justify-between">
                        <span>{status}</span>
                        <span className="font-medium">{count as number}社</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">カテゴリ上位</h3>
                  <div className="space-y-1">
                    {mockStats.topCategories.map((category: { name: string; count: number }) => (
                      <div key={category.name} className="flex justify-between">
                        <span>{category.name}</span>
                        <span className="font-medium">{category.count}社</span>
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
                {mockStats.missingCount === 0 ? (
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <div className="text-green-600 font-semibold">
                      ✅ メタデータ欠損なし
                    </div>
                  </div>
                ) : (
                  <div className="text-center p-4 bg-orange-50 rounded-lg">
                    <div className="text-orange-600 font-semibold">
                      ⚠️ メタデータ欠損: {mockStats.missingCount}件
                    </div>
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
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTestQuery(e.target.value)}
                    onKeyPress={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === "Enter" && handleTestSearch()}
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
                  {testResults.map((result) => (
                    <div key={result.id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold">
                          {result.title}
                        </h4>
                        <div className="text-sm text-gray-500">
                          スコア: {Number(result.scorePct || 0).toFixed(1)}%
                        </div>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">
                        {result.snippet}
                      </p>
                      <div className="flex gap-2">
                        <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                          ID: {result.id}
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
              <CardTitle>サンプルデータ（先頭3件）</CardTitle>
              <CardDescription>
                登録済みベンダーデータのプレビュー
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {mockVendors.map((vendor, index) => (
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
                          {vendor.type}
                        </span>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <p><strong>カテゴリ:</strong> {vendor.category?.join(", ")}</p>
                      <p><strong>上場:</strong> {vendor.listed ? "上場" : "未上場"}</p>
                      {vendor.meta && (
                        <div className="text-sm text-gray-600">
                          <p><strong>従業員規模:</strong> {vendor.meta.employees_band as string}</p>
                          <p><strong>投資家:</strong> {(vendor.meta.investors as string[])?.join(", ")}</p>
                        </div>
                      )}
                    </div>
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
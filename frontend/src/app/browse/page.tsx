"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";

interface Vendor {
  id: string;
  name: string;
  status: string;
  listed: string;
  type: string;
  use_cases: string[];
  url?: string;
}

interface Facets {
  status: Record<string, number>;
  listed: Record<string, number>;
  type: Record<string, number>;
  use_cases: Record<string, number>;
}

export default function BrowsePage() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [facets, setFacets] = useState<Facets>({
    status: {},
    listed: {},
    type: {},
    use_cases: {}
  });
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: [] as string[],
    listed: [] as string[],
    type: [] as string[],
    use_cases: [] as string[]
  });
  const [clickedCard, setClickedCard] = useState<{key: string, value: string} | null>(null);

  // モックデータの生成
  useEffect(() => {
    const mockVendors: Vendor[] = [
      {
        id: "vendor_1",
        name: "LiberCraft",
        status: "面談済",
        listed: "未上場",
        type: "スクラッチ",
        use_cases: ["機械学習", "最適化"],
        url: "https://libercraft.com"
      },
      {
        id: "vendor_2",
        name: "TechCorp",
        status: "未面談",
        listed: "上場",
        type: "SaaS",
        use_cases: ["クラウド", "インフラ"]
      },
      {
        id: "vendor_3",
        name: "DataSoft",
        status: "面談済",
        listed: "未上場",
        type: "SI",
        use_cases: ["データ分析", "BI"]
      }
    ];

    // ファセットの計算
    const newFacets: Facets = {
      status: {},
      listed: {},
      type: {},
      use_cases: {}
    };

    mockVendors.forEach(vendor => {
      newFacets.status[vendor.status] = (newFacets.status[vendor.status] || 0) + 1;
      newFacets.listed[vendor.listed] = (newFacets.listed[vendor.listed] || 0) + 1;
      newFacets.type[vendor.type] = (newFacets.type[vendor.type] || 0) + 1;
      vendor.use_cases.forEach(useCase => {
        newFacets.use_cases[useCase] = (newFacets.use_cases[useCase] || 0) + 1;
      });
    });

    setVendors(mockVendors);
    setFacets(newFacets);
    setLoading(false);
  }, []);

  const handleCardClick = (key: string, value: string) => {
    setClickedCard({key, value});
  };

  const handleFilterChange = (category: keyof typeof filters, value: string) => {
    setFilters(prev => ({
      ...prev,
      [category]: prev[category].includes(value)
        ? prev[category].filter(v => v !== value)
        : [...prev[category], value]
    }));
  };

  const clearFilters = () => {
    setFilters({
      status: [],
      listed: [],
      type: [],
      use_cases: []
    });
    setClickedCard(null);
  };

  const filteredVendors = vendors.filter(vendor => {
    if (filters.status.length > 0 && !filters.status.includes(vendor.status)) return false;
    if (filters.listed.length > 0 && !filters.listed.includes(vendor.listed)) return false;
    if (filters.type.length > 0 && !filters.type.includes(vendor.type)) return false;
    if (filters.use_cases.length > 0 && !vendor.use_cases.some(uc => filters.use_cases.includes(uc))) return false;
    
    if (clickedCard) {
      if (clickedCard.key === "use_cases") {
        return vendor.use_cases.includes(clickedCard.value);
      }
      return (vendor as any)[clickedCard.key] === clickedCard.value;
    }
    
    return true;
  });

  if (loading) {
    return <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">読み込み中...</p>
      </div>
    </div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            📊 ベンダーブラウズ
          </h1>
          <p className="text-gray-600">
            分類別にベンダー情報を閲覧・検索できます
          </p>
        </div>

        <div className="grid lg:grid-cols-4 gap-8">
          {/* サイドバー - フィルタ */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>フィルタ</CardTitle>
                <Button variant="outline" size="sm" onClick={clearFilters}>
                  クリア
                </Button>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* 面談ステータス */}
                <div>
                  <Label className="text-sm font-medium">面談ステータス</Label>
                  <div className="mt-2 space-y-2">
                    {Object.entries(facets.status).map(([status, count]) => (
                      <label key={status} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={filters.status.includes(status)}
                          onChange={() => handleFilterChange("status", status)}
                          className="rounded"
                        />
                        <span className="text-sm">{status} ({count})</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* 上場区分 */}
                <div>
                  <Label className="text-sm font-medium">上場区分</Label>
                  <div className="mt-2 space-y-2">
                    {Object.entries(facets.listed).map(([listed, count]) => (
                      <label key={listed} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={filters.listed.includes(listed)}
                          onChange={() => handleFilterChange("listed", listed)}
                          className="rounded"
                        />
                        <span className="text-sm">{listed} ({count})</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* タイプ */}
                <div>
                  <Label className="text-sm font-medium">タイプ</Label>
                  <div className="mt-2 space-y-2">
                    {Object.entries(facets.type).map(([type, count]) => (
                      <label key={type} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={filters.type.includes(type)}
                          onChange={() => handleFilterChange("type", type)}
                          className="rounded"
                        />
                        <span className="text-sm">{type} ({count})</span>
                      </label>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* メインコンテンツ */}
          <div className="lg:col-span-3">
            {/* 集計カード */}
            <div className="mb-8">
              <h2 className="text-xl font-semibold mb-4">集計（クリックでドリルダウン）</h2>
              <div className="grid md:grid-cols-3 gap-4">
                {/* 面談ステータス */}
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">面談ステータス</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {Object.entries(facets.status).map(([status, count]) => (
                        <Button
                          key={status}
                          variant="outline"
                          size="sm"
                          className="w-full justify-between"
                          onClick={() => handleCardClick("status", status)}
                        >
                          {status}: {count}社
                        </Button>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* 上場区分 */}
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">上場区分</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {Object.entries(facets.listed).map(([listed, count]) => (
                        <Button
                          key={listed}
                          variant="outline"
                          size="sm"
                          className="w-full justify-between"
                          onClick={() => handleCardClick("listed", listed)}
                        >
                          {listed}: {count}社
                        </Button>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* タイプ */}
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">タイプ</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {Object.entries(facets.type).map(([type, count]) => (
                        <Button
                          key={type}
                          variant="outline"
                          size="sm"
                          className="w-full justify-between"
                          onClick={() => handleCardClick("type", type)}
                        >
                          {type}: {count}社
                        </Button>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>

            {/* ドリルダウン表示 */}
            {clickedCard && (
              <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-blue-800">
                  ドリルダウン: {clickedCard.key} = {clickedCard.value}
                </p>
              </div>
            )}

            {/* ベンダー一覧 */}
            <div>
              <h2 className="text-xl font-semibold mb-4">
                該当: {filteredVendors.length}社
              </h2>
              <div className="space-y-4">
                {filteredVendors.map((vendor) => (
                  <Card key={vendor.id}>
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle className="text-lg">{vendor.name}</CardTitle>
                          <CardDescription>
                            {vendor.status} / {vendor.listed} / {vendor.type}
                          </CardDescription>
                        </div>
                        <div className="text-right text-sm space-y-1">
                          <div className="bg-blue-100 text-blue-800 px-2 py-1 rounded">
                            {vendor.status}
                          </div>
                          <div className="bg-green-100 text-green-800 px-2 py-1 rounded">
                            {vendor.type}
                          </div>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <p><strong>得意分野:</strong> {vendor.use_cases.join(", ")}</p>
                        {vendor.url && (
                          <p><strong>URL:</strong> <a href={vendor.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{vendor.url}</a></p>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

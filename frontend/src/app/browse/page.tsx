"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import type { Vendor, Facets, VendorStatus } from "@/types";
import { STATUS_LABEL } from "@/types";

interface VendorWithDetails extends Vendor {
  url?: string;
  employees_band?: string;
  investors?: string[];
  is_scratch?: boolean;
  deployment?: string;
  price_range?: string;
  industries?: string[];
  departments?: string[];
  listed?: boolean;
  type?: string;
}

interface FacetsWithCounts {
  status: Record<string, number>;
  listed: Record<string, number>;
  type: Record<string, number>;
  use_cases: Record<string, number>;
}

export default function BrowsePage() {
  const [vendors, setVendors] = useState<VendorWithDetails[]>([]);
  const [facets, setFacets] = useState<FacetsWithCounts>({
    status: {},
    listed: {},
    type: {},
    use_cases: {}
  });
  const [clickedCard, setClickedCard] = useState<{key: string, value: string} | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedFilters, setSelectedFilters] = useState<Facets>({});

  // モックデータの生成
  const mockVendors: VendorWithDetails[] = [
    {
      id: "vendor_1",
      name: "LiberCraft",
      status: "ok",
      listed: false,
      type: "スクラッチ",
      category: ["スクラッチ"],
      url: "https://libercraft.com",
      employees_band: "1-10",
      investors: ["投資家A"],
      is_scratch: true,
      deployment: "ハイブリッド",
      price_range: "高",
      industries: ["製造業", "金融"],
      departments: ["法務", "人事"]
    },
    {
      id: "vendor_2",
      name: "TechCorp",
      status: "unknown",
      listed: true,
      type: "SaaS",
      category: ["SaaS"],
      employees_band: "100-500",
      investors: ["投資家B", "投資家C"],
      is_scratch: false,
      deployment: "クラウド",
      price_range: "中",
      industries: ["IT", "金融"],
      departments: ["IT", "営業"]
    },
    {
      id: "vendor_3",
      name: "DataSoft",
      status: "ok",
      listed: false,
      type: "SI",
      category: ["SI"],
      employees_band: "50-100",
      investors: ["投資家D"],
      is_scratch: false,
      deployment: "オンプレ",
      price_range: "低",
      industries: ["製造業", "小売"],
      departments: ["IT", "経理"]
    },
    {
      id: "vendor_4",
      name: "CloudTech",
      status: "unknown",
      listed: true,
      type: "SaaS",
      category: ["SaaS"],
      employees_band: "500+",
      investors: ["投資家E", "投資家F"],
      is_scratch: false,
      deployment: "クラウド",
      price_range: "高",
      industries: ["IT", "金融", "製造業"],
      departments: ["IT", "営業", "マーケティング"]
    }
  ];

  // ファセットの計算
  const calculateFacets = (vendorList: VendorWithDetails[]): FacetsWithCounts => {
    const newFacets: FacetsWithCounts = {
      status: {},
      listed: {},
      type: {},
      use_cases: {}
    };

    vendorList.forEach(vendor => {
      // ステータス
      const status = vendor.status || "不明";
      newFacets.status[status] = (newFacets.status[status] || 0) + 1;

      // 上場区分
      const listed = vendor.listed ? "上場" : "未上場";
      newFacets.listed[listed] = (newFacets.listed[listed] || 0) + 1;

      // タイプ
      const type = vendor.type || "その他";
      newFacets.type[type] = (newFacets.type[type] || 0) + 1;

      // カテゴリ（use_casesとして扱う）
      vendor.category?.forEach(cat => {
        newFacets.use_cases[cat] = (newFacets.use_cases[cat] || 0) + 1;
      });
    });

    return newFacets;
  };

  // 初期化
  if (vendors.length === 0) {
    setVendors(mockVendors);
    setFacets(calculateFacets(mockVendors));
  }

  // フィルタリング
  const filteredVendors = vendors.filter(vendor => {
    // 検索語によるフィルタ
    if (searchTerm && !vendor.name.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }

    // クリックされたカードによるフィルタ
    if (clickedCard) {
      if (clickedCard.key === "status") {
        return vendor.status === clickedCard.value;
      }
      if (clickedCard.key === "listed") {
        return (vendor.listed ? "上場" : "未上場") === clickedCard.value;
      }
      if (clickedCard.key === "type") {
        return vendor.type === clickedCard.value;
      }
      if (clickedCard.key === "use_cases") {
        return vendor.category?.includes(clickedCard.value);
      }
    }

    // 選択されたフィルタによるフィルタ
    if (selectedFilters.status && selectedFilters.status.length > 0) {
      if (!vendor.status || !selectedFilters.status.includes(vendor.status)) {
        return false;
      }
    }

    if (selectedFilters.type && selectedFilters.type.length > 0) {
      if (!vendor.type || !selectedFilters.type.includes(vendor.type)) {
        return false;
      }
    }

    return true;
  });

  const handleFilterChange = (filterType: keyof Facets, value: string, checked: boolean) => {
    setSelectedFilters(prev => {
      const currentValues = prev[filterType] || [];
      if (checked) {
        return {
          ...prev,
          [filterType]: [...currentValues, value]
        };
      } else {
        return {
          ...prev,
          [filterType]: currentValues.filter(v => v !== value)
        };
      }
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4 max-w-7xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            📊 ベンダーブラウズ
          </h1>
          <p className="text-gray-600">
            分類別にベンダー情報を閲覧・検索・フィルタリング
          </p>
        </div>

        <div className="grid lg:grid-cols-4 gap-8">
          {/* サイドバー - フィルタ */}
          <div className="lg:col-span-1 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">検索・フィルタ</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="search">ベンダー名検索</Label>
                  <Input
                    id="search"
                    placeholder="ベンダー名で検索"
                    value={searchTerm}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
                  />
                </div>

                <div>
                  <Label>ステータス</Label>
                  <div className="space-y-2 mt-2">
                    {Object.entries(facets.status).map(([status, count]) => (
                      <div key={status} className="flex items-center space-x-2">
                        <Checkbox
                          id={`status-${status}`}
                          checked={selectedFilters.status?.includes(status as VendorStatus) || false}
                          onCheckedChange={(checked: boolean) => handleFilterChange("status", status, checked)}
                        />
                        <Label htmlFor={`status-${status}`} className="text-sm">
                          {status} ({count})
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <Label>タイプ</Label>
                  <div className="space-y-2 mt-2">
                    {Object.entries(facets.type).map(([type, count]) => (
                      <div key={type} className="flex items-center space-x-2">
                        <Checkbox
                          id={`type-${type}`}
                          checked={selectedFilters.type?.includes(type) || false}
                          onCheckedChange={(checked: boolean) => handleFilterChange("type", type, checked)}
                        />
                        <Label htmlFor={`type-${type}`} className="text-sm">
                          {type} ({count})
                        </Label>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* メインコンテンツ */}
          <div className="lg:col-span-3 space-y-6">
            {/* 集計カード */}
            <div>
              <h2 className="text-xl font-semibold mb-4">集計（クリックでドリルダウン）</h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
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
                          onClick={() => setClickedCard({key: "status", value: status})}
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
                          onClick={() => setClickedCard({key: "listed", value: listed})}
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
                          onClick={() => setClickedCard({key: "type", value: type})}
                        >
                          {type}: {count}社
                        </Button>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* カテゴリ */}
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">カテゴリ</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {Object.entries(facets.use_cases).map(([category, count]) => (
                        <Button
                          key={category}
                          variant="outline"
                          size="sm"
                          className="w-full justify-between"
                          onClick={() => setClickedCard({key: "use_cases", value: category})}
                        >
                          {category}: {count}社
                        </Button>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>

            {/* ドリルダウン表示 */}
            {clickedCard && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex justify-between items-center">
                  <p className="text-blue-800">
                    ドリルダウン: {clickedCard.key} = {clickedCard.value}
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setClickedCard(null)}
                  >
                    クリア
                  </Button>
                </div>
              </div>
            )}

            {/* ベンダー一覧 */}
            <div>
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold">
                  該当: {filteredVendors.length}社
                </h2>
                {(clickedCard || searchTerm || Object.values(selectedFilters).some(f => f && f.length > 0)) && (
                  <Button
                    variant="outline"
                    onClick={() => {
                      setClickedCard(null);
                      setSearchTerm("");
                      setSelectedFilters({});
                    }}
                  >
                    フィルタクリア
                  </Button>
                )}
              </div>

              <div className="space-y-4">
                {filteredVendors.map((vendor) => (
                  <Card key={vendor.id}>
                    <CardContent className="p-6">
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="text-lg font-semibold">{vendor.name}</h3>
                          <p className="text-sm text-gray-600">
                            {STATUS_LABEL[vendor.status ?? "unknown"]} / {vendor.listed ? "上場" : "未上場"} / {vendor.type}
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Badge variant="secondary">{STATUS_LABEL[vendor.status ?? "unknown"]}</Badge>
                          <Badge variant="outline">{vendor.type}</Badge>
                          {vendor.listed && <Badge variant="default">上場</Badge>}
                        </div>
                      </div>

                      <div className="grid md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <p><strong>カテゴリ:</strong> {vendor.category?.join(", ")}</p>
                          {vendor.url && (
                            <p>
                              <strong>URL:</strong>{" "}
                              <a
                                href={vendor.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:underline"
                              >
                                {vendor.url}
                              </a>
                            </p>
                          )}
                          <p><strong>従業員規模:</strong> {vendor.employees_band}</p>
                          <p><strong>デプロイ:</strong> {vendor.deployment}</p>
                        </div>
                        <div className="space-y-2">
                          <p><strong>価格帯:</strong> {vendor.price_range}</p>
                          <p><strong>業界:</strong> {vendor.industries?.join(", ")}</p>
                          <p><strong>部門:</strong> {vendor.departments?.join(", ")}</p>
                          <p><strong>投資家:</strong> {vendor.investors?.join(", ")}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {filteredVendors.length === 0 && (
                <div className="text-center py-12">
                  <p className="text-gray-500 text-lg">
                    条件に一致するベンダーが見つかりませんでした
                  </p>
                  <Button
                    variant="outline"
                    className="mt-4"
                    onClick={() => {
                      setClickedCard(null);
                      setSearchTerm("");
                      setSelectedFilters({});
                    }}
                  >
                    フィルタをクリア
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
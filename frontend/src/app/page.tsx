"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { KBStats, Vendor } from "@/types";
import type { SearchHit, Metadata } from "@/lib/types";
import { searchApi } from "@/lib/fetcher";

// 型定義
interface SearchResultData {
  result: string;
  source_documents?: Array<{
    page_content: string;
    metadata: Record<string, unknown>;
  }>;
}

interface VendorWithDoc extends Vendor {
  url?: string;
  employees_band?: string;
  investors?: string[];
  is_scratch?: boolean;
  deployment?: string;
  price_range?: string;
  industries?: string[];
  departments?: string[];
  doc: {
    page_content: string;
  };
}

interface FacetsWithCounts {
  status: Record<string, number>;
  listed: Record<string, number>;
  type: Record<string, number>;
  use_cases: Record<string, number>;
}

export default function MainPage() {
  // 状態管理
  const [activeTab, setActiveTab] = useState("search");
  const [apiKey, setApiKey] = useState("");
  const [dataLoaded, setDataLoaded] = useState(false);
  const [loading, setLoading] = useState(false);
  
  // パラメータ設定
  const [topK, setTopK] = useState(8);
  const [chunkSize, setChunkSize] = useState(0);
  const [chunkOverlap, setChunkOverlap] = useState(0);
  const [useMmr, setUseMmr] = useState(true);
  const [scoreThreshold, setScoreThreshold] = useState(0.0);
  const [embedModel, setEmbedModel] = useState("text-embedding-3-small");
  const [chatModel, setChatModel] = useState("gpt-3.5-turbo");
  const [temperature, setTemperature] = useState(0.0);
  
  // 検索関連
  const [query, setQuery] = useState("");
  const [searchResult, setSearchResult] = useState<SearchResultData | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  
  // KB関連
  const [kbStats, setKbStats] = useState<KBStats | null>(null);
  const [vendors, setVendors] = useState<VendorWithDoc[]>([]);
  
  // ブラウズ関連
  const [facets, setFacets] = useState<FacetsWithCounts>({
    status: {},
    listed: {},
    type: {},
    use_cases: {}
  });
  const [clickedCard, setClickedCard] = useState<{key: string, value: string} | null>(null);

  // 検索実行
  const handleSearch = async () => {
    if (!query.trim()) return;

    setSearchLoading(true);
    try {
      // RAG API呼び出し
      const { hits } = await searchApi(query, 8, false).catch(() => ({ hits: [] as SearchHit[] }));

      if (!hits.length) {
        throw new Error("検索結果がありません");
      }

      // APIレスポンスをSearchResultData形式に変換
      const searchResult: SearchResultData = {
        result: hits.map(hit => 
          `**${hit.title}** (スコア: ${((hit.score || 0) * 100).toFixed(1)}%)\n${hit.snippet || ''}`
        ).join('\n\n'),
        source_documents: hits.map(hit => ({
          page_content: hit.snippet || '',
          metadata: {
            vendor_id: hit.id,
            name: hit.title,
            status: "ok", // 防御的にデフォルト値を設定
            category: "unknown"
          }
        }))
      };

      setSearchResult(searchResult);
    } catch (error) {
      const msg = error instanceof Error ? error.message : String(error);
      console.error("検索エラー:", error);
      // エラー時のフォールバック
      setSearchResult({
        result: `検索中にエラーが発生しました: ${msg}`,
        source_documents: []
      });
    } finally {
      setSearchLoading(false);
    }
  };

  // データ読み込み
  const handleLoadData = async () => {
    setLoading(true);
    try {
      // モックデータの生成（実際はAPIから取得）
      const mockVendors: VendorWithDoc[] = [
        {
          id: "V-LiberCraft",
          name: "LiberCraft",
          status: "面談済",
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
          departments: ["法務", "人事"],
          meta: {
            employees_band: "1-10",
            investors: ["投資家A"],
            is_scratch: true,
            deployment: "ハイブリッド",
            price_range: "高",
            industries: ["製造業", "金融"],
            departments: ["法務", "人事"]
          },
          doc: { page_content: "LiberCraftの詳細情報..." }
        },
        {
          id: "V-TechCorp",
          name: "TechCorp",
          status: "未面談",
          listed: true,
          type: "SaaS",
          category: ["SaaS"],
          employees_band: "100-500",
          investors: ["投資家B", "投資家C"],
          is_scratch: false,
          deployment: "クラウド",
          price_range: "中",
          industries: ["IT", "金融"],
          departments: ["IT", "営業"],
          meta: {
            employees_band: "100-500",
            investors: ["投資家B", "投資家C"],
            is_scratch: false,
            deployment: "クラウド",
            price_range: "中",
            industries: ["IT", "金融"],
            departments: ["IT", "営業"]
          },
          doc: { page_content: "TechCorpの詳細情報..." }
        }
      ];

      // ファセットの計算
      const newFacets: FacetsWithCounts = {
        status: {},
        listed: {},
        type: {},
        use_cases: {}
      };

      mockVendors.forEach(vendor => {
        newFacets.status[vendor.status || "不明"] = (newFacets.status[vendor.status || "不明"] || 0) + 1;
        newFacets.listed[vendor.listed ? "上場" : "未上場"] = (newFacets.listed[vendor.listed ? "上場" : "未上場"] || 0) + 1;
        newFacets.type[vendor.type || "その他"] = (newFacets.type[vendor.type || "その他"] || 0) + 1;
        // use_casesは別途計算
      });

      // KB統計の計算
      const stats: KBStats = {
        totalVendors: mockVendors.length,
        missingCount: 0,
        byFormat: {
          "JSON": 2
        },
        byStatus: newFacets.status,
        topCategories: [
          { name: "スクラッチ", count: 1 },
          { name: "SaaS", count: 1 }
        ]
      };

      setVendors(mockVendors);
      setFacets(newFacets);
      setKbStats(stats);
      setDataLoaded(true);
      
    } catch (error) {
      console.error("データ読み込みエラー:", error);
    } finally {
      setLoading(false);
    }
  };

  // フィルタされたベンダー
  const filteredVendors = vendors.filter(vendor => {
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
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex">
        {/* サイドバー */}
        <div className="w-80 bg-white shadow-lg p-6 overflow-y-auto">
          <div className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold mb-4">⚙️ パラメータ</h2>
              
              <div className="space-y-4">
                <div>
                  <Label htmlFor="apiKey">OpenAI API Key</Label>
                  <Input
                    id="apiKey"
                    type="password"
                    placeholder="sk-..."
                    value={apiKey}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setApiKey(e.target.value)}
                  />
                </div>

                <div>
                  <Label htmlFor="topK">Top K（取得文書数）</Label>
                  <Input
                    id="topK"
                    type="number"
                    min="1"
                    max="15"
                    value={topK}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTopK(parseInt(e.target.value))}
                  />
                </div>

                <div>
                  <Label htmlFor="chunkSize">チャンクサイズ</Label>
                  <Input
                    id="chunkSize"
                    type="number"
                    min="0"
                    max="2000"
                    value={chunkSize}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setChunkSize(parseInt(e.target.value))}
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    0 = ベンダー単位のみ
                  </p>
                </div>

                <div>
                  <Label htmlFor="chunkOverlap">チャンクオーバーラップ</Label>
                  <Input
                    id="chunkOverlap"
                    type="number"
                    min="0"
                    max="500"
                    value={chunkOverlap}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setChunkOverlap(parseInt(e.target.value))}
                  />
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="useMmr"
                    checked={useMmr}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setUseMmr(e.target.checked)}
                  />
                  <Label htmlFor="useMmr">MMRを使う（多様性）</Label>
                </div>

                <div>
                  <Label htmlFor="scoreThreshold">スコアしきい値</Label>
                  <Input
                    id="scoreThreshold"
                    type="number"
                    min="0.0"
                    max="1.0"
                    step="0.05"
                    value={scoreThreshold}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setScoreThreshold(parseFloat(e.target.value))}
                  />
                </div>

                <div>
                  <Label htmlFor="embedModel">Embeddings</Label>
                  <select
                    id="embedModel"
                    value={embedModel}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setEmbedModel(e.target.value)}
                    className="w-full p-2 border rounded"
                  >
                    <option value="text-embedding-3-small">text-embedding-3-small</option>
                    <option value="text-embedding-3-large">text-embedding-3-large</option>
                  </select>
                </div>

                <div>
                  <Label htmlFor="chatModel">Chat Model</Label>
                  <select
                    id="chatModel"
                    value={chatModel}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setChatModel(e.target.value)}
                    className="w-full p-2 border rounded"
                  >
                    <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
                    <option value="gpt-4o-mini">gpt-4o-mini</option>
                  </select>
                </div>

                <div>
                  <Label htmlFor="temperature">Temperature</Label>
                  <Input
                    id="temperature"
                    type="number"
                    min="0.0"
                    max="1.0"
                    step="0.1"
                    value={temperature}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTemperature(parseFloat(e.target.value))}
                  />
                </div>
              </div>
            </div>

            <div className="border-t pt-6">
              <h3 className="text-lg font-semibold mb-4">📁 データ読み込み</h3>
              <Button 
                onClick={handleLoadData} 
                disabled={loading}
                className="w-full"
              >
                {loading ? "読み込み中..." : "📥 データ読み込み / 再インデックス"}
              </Button>
              {dataLoaded && (
                <p className="text-sm text-green-600 mt-2">
                  ✅ データ読み込み完了
                </p>
              )}
            </div>
          </div>
        </div>

        {/* メインコンテンツ */}
        <div className="flex-1 p-6">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="search">🔎 検索UI</TabsTrigger>
              <TabsTrigger value="kb">📚 KBビューア</TabsTrigger>
              <TabsTrigger value="browse">📊 ブラウズ</TabsTrigger>
            </TabsList>

            {/* 検索UIタブ */}
            <TabsContent value="search" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>質問を入力</CardTitle>
                  <CardDescription>
                    自然言語でベンダー情報を検索できます
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label htmlFor="query">検索クエリ</Label>
                    <Input
                      id="query"
                      placeholder="例: 法務カテゴリで価格帯が低いベンダーを教えて"
                      value={query}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQuery(e.target.value)}
                      onKeyPress={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === "Enter" && handleSearch()}
                    />
                  </div>
                  <Button 
                    onClick={handleSearch} 
                    disabled={searchLoading || !query.trim()}
                    className="w-full"
                  >
                    {searchLoading ? "検索中..." : "検索"}
                  </Button>

                  {searchResult && (
                    <div className="mt-6 space-y-4">
                      <Card>
                        <CardHeader>
                          <CardTitle>📝 回答</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="whitespace-pre-wrap">
                            {searchResult.result}
                          </div>
                        </CardContent>
                      </Card>

                      {searchResult.source_documents && (
                        <Card>
                          <CardHeader>
                            <CardTitle>📚 参照ソース抜粋（上位3件）</CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-4">
                            {searchResult.source_documents.slice(0, 3).map((doc, index) => (
                              <div key={index} className="border rounded p-4">
                                <h4 className="font-semibold mb-2">
                                  ソース {index + 1} - {doc.metadata.vendor_id as string}
                                </h4>
                                <p className="text-sm text-gray-600 mb-2">
                                  {doc.page_content.substring(0, 800)}
                                  {doc.page_content.length > 800 && "..."}
                                </p>
                                <div className="text-xs text-gray-500">
                                  <pre>{JSON.stringify(doc.metadata, null, 2)}</pre>
                                </div>
                              </div>
                            ))}
                          </CardContent>
                        </Card>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            {/* KBビューアタブ */}
            <TabsContent value="kb" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>📚 ナレッジベースビューア</CardTitle>
                  <CardDescription>
                    登録済みデータの統計情報と一覧
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {!dataLoaded ? (
                    <p className="text-gray-500">
                      データが読み込まれていません。左のサイドバーから「データ読み込み」を実行してください。
                    </p>
                  ) : kbStats ? (
                    <div className="space-y-6">
                      {/* サマリ情報 */}
                      <div className="grid grid-cols-4 gap-4">
                        <div className="text-center p-4 bg-blue-50 rounded">
                          <div className="text-2xl font-bold text-blue-600">
                            {kbStats.totalVendors}
                          </div>
                          <div className="text-blue-800">総ベンダー数</div>
                        </div>
                        <div className="text-center p-4 bg-orange-50 rounded">
                          <div className="text-2xl font-bold text-orange-600">
                            {kbStats.missingCount}
                          </div>
                          <div className="text-orange-800">vendor_id欠落</div>
                        </div>
                        <div className="text-center p-4 bg-green-50 rounded">
                          <div className="text-2xl font-bold text-green-600">
                            {kbStats.byFormat["JSON"] || 0}
                          </div>
                          <div className="text-green-800">JSON形式</div>
                        </div>
                        <div className="text-center p-4 bg-purple-50 rounded">
                          <div className="text-2xl font-bold text-purple-600">
                            {kbStats.byFormat["Markdown"] || 0}
                          </div>
                          <div className="text-purple-800">Markdown形式</div>
                        </div>
                      </div>

                      {/* ステータス別件数 */}
                      <div>
                        <h3 className="text-lg font-semibold mb-4">📊 ステータス別件数</h3>
                        <div className="space-y-2">
                          {Object.entries(kbStats.byStatus).map(([status, count]) => (
                            <div key={status} className="flex justify-between p-2 bg-gray-50 rounded">
                              <span>{status}</span>
                              <span className="font-medium">{count}件</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* カテゴリ上位 */}
                      <div>
                        <h3 className="text-lg font-semibold mb-4">📊 カテゴリ上位</h3>
                        <div className="space-y-2">
                          {kbStats.topCategories.map((category) => (
                            <div key={category.name} className="flex justify-between p-2 bg-gray-50 rounded">
                              <span>{category.name}</span>
                              <span className="font-medium">{category.count}件</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* メタデータ欠損 */}
                      <div>
                        {kbStats.missingCount === 0 ? (
                          <div className="p-4 bg-green-50 border border-green-200 rounded">
                            <p className="text-green-800">✅ メタデータ欠損なし</p>
                          </div>
                        ) : (
                          <div className="p-4 bg-orange-50 border border-orange-200 rounded">
                            <p className="text-orange-800">
                              メタデータ欠損: {kbStats.missingCount}件
                            </p>
                          </div>
                        )}
                      </div>

                      {/* ドキュメント一覧 */}
                      <div>
                        <h3 className="text-lg font-semibold mb-4">📋 ドキュメント一覧</h3>
                        <div className="space-y-4">
                          {vendors.slice(0, 10).map((vendor, index) => (
                            <div key={vendor.id} className="border rounded p-4">
                              <div className="flex justify-between items-start mb-2">
                                <h4 className="font-semibold">
                                  #{index + 1} {vendor.id} — {vendor.name}
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
                              <p className="text-sm text-gray-600">
                                {vendor.doc.page_content.substring(0, 200)}...
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : null}
                </CardContent>
              </Card>
            </TabsContent>

            {/* ブラウズタブ */}
            <TabsContent value="browse" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>📊 ブラウズ</CardTitle>
                  <CardDescription>
                    分類別にベンダー情報を閲覧・検索
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {!dataLoaded ? (
                    <p className="text-gray-500">
                      データが読み込まれていません。左のサイドバーから「データ読み込み」を実行してください。
                    </p>
                  ) : (
                    <div className="space-y-6">
                      {/* 集計カード */}
                      <div>
                        <h3 className="text-lg font-semibold mb-4">集計（クリックでドリルダウン）</h3>
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
                        </div>
                      </div>

                      {/* ドリルダウン表示 */}
                      {clickedCard && (
                        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                          <p className="text-blue-800">
                            ドリルダウン: {clickedCard.key} = {clickedCard.value}
                          </p>
                        </div>
                      )}

                      {/* ベンダー一覧 */}
                      <div>
                        <h3 className="text-lg font-semibold mb-4">
                          該当: {filteredVendors.length}社
                        </h3>
                        <div className="space-y-4">
                          {filteredVendors.map((vendor) => (
                            <div key={vendor.id} className="border rounded p-4">
                              <div className="flex justify-between items-start mb-2">
                                <div>
                                  <h4 className="font-semibold">{vendor.name}</h4>
                                  <p className="text-sm text-gray-600">
                                    {vendor.status} / {vendor.listed ? "上場" : "未上場"} / {vendor.type}
                                  </p>
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
                              <div className="space-y-2">
                                <p><strong>カテゴリ:</strong> {vendor.category?.join(", ")}</p>
                                {vendor.url && (
                                  <p><strong>URL:</strong> <a href={vendor.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">{vendor.url}</a></p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
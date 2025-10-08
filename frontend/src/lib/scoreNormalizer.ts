// スコア正規化ユーティリティ
export type RawResult = { 
  text?: string; 
  score: number; 
  metadata?: Record<string, any>;
  id?: string;
  title?: string;
  snippet?: string;
  url?: string;
  [k: string]: any;
};

export type ViewResult = RawResult & { scorePct: number };

/**
 * 検索結果のスコアを0-100%に正規化する
 * @param results 生の検索結果配列
 * @returns 正規化されたスコアを含む結果配列
 */
export function normalizeSearchResults(results: RawResult[]): ViewResult[] {
  if (results.length === 0) return [];
  
  // コサイン類似度の絶対値を0-100%に変換（min-max正規化を削除）
  const normalized: ViewResult[] = results.map(r => ({
    ...r,
    scorePct: Math.round(Number(r.score) * 1000) / 10  // 0.832 → 83.2%
  }));
  
  // スコア降順でソート
  return normalized.sort((a, b) => b.scorePct - a.scorePct);
}

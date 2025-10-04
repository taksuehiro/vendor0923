/**
 * App-wide lightweight types used by UI pages.
 * Keep in sync with backend contracts as they evolve.
 */

import type { VendorStatus } from "./types/vendor";

export type Vendor = {
  id: string;
  name: string;
  status?: VendorStatus;
  listed?: boolean;
  type?: string;
  category?: string[];
  meta?: Record<string, unknown>;
};

export type Facets = {
  category?: string[];
  status?: VendorStatus[];
  type?: string[];
};

export type KBStats = {
  documents?: number;
  vendors?: number;
  lastIndexedAt?: string;
  // 追加フィールド
  totalVendors: number;
  missingCount: number;
  byFormat: Record<string, number>;
  byStatus: Record<string, number>;
  topCategories: Array<{
    name: string;
    count: number;
  }>;
};

// API types defined locally
export type ResponseMetadata = { total?: number; provider?: string; [k: string]: unknown };
export type SearchHit = {
  id: string;
  title: string;
  score?: number;
  snippet?: string;
  url?: string;
  metadata?: Record<string, unknown>; // per-hit freeform
};
export type SearchResponse = { hits: SearchHit[]; metadata?: ResponseMetadata };

// SearchResult interface for search results
export interface SearchResult {
  id: string;
  title: string;
  snippet: string;
  content?: string;
  score?: number;
  scorePct?: number;
  url?: string;
  status?: string;
  category?: string[];
  vendor_id?: string;
  // metadataフィールドの型定義を追加
  metadata?: {
    status?: string;
    category?: string;
    [key: string]: unknown;
  };
}

// ViewResult interface for search results display
export interface ViewResult {
  id: number;
  text: string;
  scorePct: number;   // 表示用の正規化済みスコア
  rawScore: number;   // APIから返る生スコア
  metadata?: any;
}

// VendorWithDetails interface for browse page
export interface VendorWithDetails extends Vendor {
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

// Re-export VendorStatus for external use
export type { VendorStatus } from "./types/vendor";

// Status labels for display
export const STATUS_LABEL: Record<VendorStatus, string> = {
  uncontacted: "未接触",
  interviewed: "面談済",
  not_interviewed: "未面談",
  proposing: "提案中",
  poc: "PoC",
  contracted: "契約済",
  on_hold: "保留",
  lost: "失注",
  unknown: "不明"
};
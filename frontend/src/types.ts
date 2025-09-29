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

// Re-export API types so imports can use either "@/types" or "@/lib/types".
export { type SearchHit, type Metadata, type ApiResponse } from "@/lib/types";

// SearchResponse type for fetcher
import type { SearchHit as LibSearchHit, Metadata as LibMetadata } from "@/lib/types";
export type SearchResponse = {
  hits: LibSearchHit[];
  metadata?: LibMetadata;
};

// SearchResult interface for search results
export interface SearchResult {
  id: string;
  title: string;
  snippet: string;
  content?: string;
  score?: number;
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
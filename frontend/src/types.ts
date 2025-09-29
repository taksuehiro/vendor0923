/**
 * App-wide lightweight types used by UI pages.
 * Keep in sync with backend contracts as they evolve.
 */

export type VendorStatus = "ok" | "error" | "unknown";

export type Vendor = {
  id: string;
  name: string;
  // optional fields (UI can render even if undefined)
  category?: string[];
  status?: VendorStatus;
  score?: number;
  // 追加フィールド
  listed?: boolean;
  type?: string;
  meta?: {
    url?: string;
    employees_band?: string;
    investors?: string[];
    [key: string]: unknown;
  };
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

// Status labels for display
export const STATUS_LABEL: Record<VendorStatus, string> = {
  ok: "面談済",
  error: "エラー",
  unknown: "不明"
};
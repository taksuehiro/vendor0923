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
};

export type Facets = {
  category?: string[];
  status?: VendorStatus[];
};

export type KBStats = {
  documents: number;
  vendors: number;
  lastIndexedAt?: string;
};

// Re-export API types so imports can use either "@/types" or "@/lib/types".
export { type SearchHit, type Metadata, type ApiResponse } from "@/lib/types";

// SearchResponse type for fetcher
export type SearchResponse = {
  hits: SearchHit[];
  metadata?: Metadata;
};

// Status labels for display
export const STATUS_LABEL: Record<VendorStatus, string> = {
  ok: "面談済",
  error: "エラー",
  unknown: "不明"
};
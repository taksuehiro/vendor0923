/**
 * App-wide lightweight types used by UI pages.
 * Keep in sync with backend contracts as they evolve.
 */

export type Vendor = {
  id: string;
  name: string;
  // optional fields (UI can render even if undefined)
  category?: string;
  status?: "ok" | "error" | "unknown";
  score?: number;
};

export type Facets = {
  categories?: string[];
  statuses?: Array<"ok" | "error" | "unknown">;
};

export type KBStats = {
  documents: number;
  vendors: number;
  lastIndexedAt?: string;
};

// Re-export API types so imports can use either "@/types" or "@/lib/types".
export type { SearchHit, Metadata, ApiResponse } from "@/lib/types";

// SearchResponse type for fetcher
export type SearchResponse = {
  hits: SearchHit[];
  metadata?: Metadata;
};

// Status labels for display
export const STATUS_LABEL: Record<"ok" | "error" | "unknown", string> = {
  ok: "面談済",
  error: "エラー",
  unknown: "不明"
};
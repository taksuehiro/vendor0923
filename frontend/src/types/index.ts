// src/types/index.ts
export interface SearchResult {
  id: string;
  title: string;
  score: number;
  snippet: string;
  metadata: {
    status: string;
    category: string;
  };
}

export interface SearchRequest {
  query: string;
  top_k: number;
  mmr: number;
}

export interface SearchResponse {
  hits: SearchResult[];
}

export interface KBStats {
  totalVendors: number;
  missingCount: number;
  byFormat: Record<string, number>;
  byStatus: Record<string, number>;
  topCategories: Array<{ name: string; count: number }>;
  // 追加項目があれば optional
  [k: string]: unknown;
}

export interface Vendor {
  id: string | number;
  name: string;
  status?: string;
  listed?: boolean;
  type?: string;
  category?: string[];
  meta?: Record<string, unknown>;
}

export interface Facets {
  status?: string[];
  listed?: Array<"yes" | "no">;
  type?: string[];
  category?: string[];
}

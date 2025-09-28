export interface Metadata {
  status?: string;
  latency_ms?: number;
  [k: string]: unknown;
}

export interface SearchHit {
  id: string;
  title: string;
  score: number;
  snippet: string;
  // 任意でメタ
  meta?: Record<string, unknown>;
}

export interface SearchResponse {
  hits: SearchHit[];
  metadata?: Metadata;
}

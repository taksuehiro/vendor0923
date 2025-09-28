export type Metadata = { total?: number };
export type SearchHit = {
  id: string;
  title: string;
  score: number;
  snippet: string;
  url?: string;
  // note: UI may reference status; it's optional on purpose
  status?: string;
};
export type SearchResponse = { hits: SearchHit[]; metadata?: Metadata };
// frontend/src/lib/fetcher.ts
export type SearchHit = {
  id: string;
  title: string;
  score: number;
  snippet: string;
};

type Metadata = Record<string, unknown>;
type ApiSuccess = { hits: SearchHit[]; metadata?: Metadata };
type ApiEnvelope = { data?: unknown } & Record<string, unknown>;

function isRecord(v: unknown): v is Record<string, unknown> {
  return !!v && typeof v === "object" && !Array.isArray(v);
}
function isHit(v: unknown): v is SearchHit {
  return (
    isRecord(v) &&
    typeof v.id === "string" &&
    typeof v.title === "string" &&
    typeof v.score === "number" &&
    typeof v.snippet === "string"
  );
}
function extractHits(obj: unknown): SearchHit[] {
  if (isRecord(obj) && Array.isArray((obj as ApiSuccess).hits) && (obj as ApiSuccess).hits.every(isHit)) {
    return (obj as ApiSuccess).hits;
  }
  if (isRecord(obj) && isRecord((obj as ApiEnvelope).data)) {
    const inner = (obj as ApiEnvelope).data!;
    if (isRecord(inner) && Array.isArray((inner as ApiSuccess).hits) && (inner as ApiSuccess).hits.every(isHit)) {
      return (inner as ApiSuccess).hits;
    }
  }
  return [];
}
function extractMetadata(obj: unknown): Metadata | undefined {
  if (isRecord(obj) && isRecord(obj.metadata)) return obj.metadata as Metadata;
  if (isRecord(obj) && isRecord((obj as ApiEnvelope).data)) {
    const data = (obj as ApiEnvelope).data as Record<string, unknown>;
    if (isRecord(data.metadata)) return data.metadata as Metadata;
  }
  return undefined;
}

export async function searchApi(query: string, k = 10, use_mmr = false) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "omit",
    body: JSON.stringify({ query, k, use_mmr }),
  });

  let json: unknown;
  try {
    json = await res.json();
  } catch {
    throw new Error(`Bad JSON (HTTP ${res.status})`);
  }

  const hits = extractHits(json);
  const metadata = extractMetadata(json);
  return { httpStatus: res.status, hits, metadata };
}
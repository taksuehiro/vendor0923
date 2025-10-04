// APIベースURL結合の安全化ユーティリティ
export const apiBase = (process.env.NEXT_PUBLIC_API_BASE || "").replace(/\/$/, "");

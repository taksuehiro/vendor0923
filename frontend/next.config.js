/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',        // 静的エクスポートを有効化
  images: { unoptimized: true }, // Image最適化APIを使わない（/_next/image を呼ばない）
  // trailingSlash はお好み（リンクの末尾に / を揃えたい場合のみ true）
  // trailingSlash: true,
};
module.exports = nextConfig;

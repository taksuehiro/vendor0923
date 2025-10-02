/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: { unoptimized: true },
  eslint: { ignoreDuringBuilds: true }, // ← これでCIビルド時はlintエラー無視
};
module.exports = nextConfig;

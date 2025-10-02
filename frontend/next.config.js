/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  images: { unoptimized: true }, // 使ってもOK（最適化APIを使わない）
  eslint: { ignoreDuringBuilds: true }, // Lintで落ちないように
};
module.exports = nextConfig;
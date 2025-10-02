/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: { unoptimized: true },
  // eslint: { ignoreDuringBuilds: true }, // CIでlintエラーを無視するなら有効化
};
module.exports = nextConfig;

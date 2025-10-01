// frontend/next.config.js
const isCI = !!process.env.CI || !!process.env.AMPLIFY_BRANCH;

const nextConfig = {
  eslint: { ignoreDuringBuilds: isCI },
  typescript: { ignoreBuildErrors: isCI },
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  // src ディレクトリの設定は不要（Next.js が自動認識する）
};

module.exports = nextConfig;

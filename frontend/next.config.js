// frontend/next.config.js
const isCI = !!process.env.CI || !!process.env.AMPLIFY_BRANCH;

const nextConfig = {
  eslint: { ignoreDuringBuilds: isCI },
  typescript: { ignoreBuildErrors: isCI },
};

module.exports = nextConfig;

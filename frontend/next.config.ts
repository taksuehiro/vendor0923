import type { NextConfig } from "next";

const isCI = !!process.env.CI || !!process.env.AMPLIFY_BRANCH;

const nextConfig: NextConfig = {
  eslint: { ignoreDuringBuilds: isCI },
  typescript: { ignoreBuildErrors: isCI },
};

export default nextConfig;

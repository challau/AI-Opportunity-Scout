import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output — optimal for Vercel and containerized deployments
  output: "standalone",

  // Disable ESLint during production builds (lint separately in CI)
  eslint: {
    ignoreDuringBuilds: true,
  },

  // Disable TypeScript build errors (type-check separately)
  typescript: {
    ignoreBuildErrors: true,
  },

  // Allow images from external domains used by event crawlers
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "devfolio.co" },
      { protocol: "https", hostname: "unstop.com" },
      { protocol: "https", hostname: "*.unstop.com" },
      { protocol: "https", hostname: "github.com" },
      { protocol: "https", hostname: "*.githubusercontent.com" },
      { protocol: "https", hostname: "hackathon.io" },
      { protocol: "https", hostname: "mlh.io" },
      { protocol: "https", hostname: "*.mlh.io" },
      { protocol: "https", hostname: "hackerearth.com" },
      { protocol: "https", hostname: "*.hackerearth.com" },
      { protocol: "https", hostname: "topcoder.com" },
      { protocol: "https", hostname: "codeforces.com" },
      { protocol: "https", hostname: "*.codeforces.com" },
      { protocol: "https", hostname: "*.cloudfront.net" },
      { protocol: "https", hostname: "*.s3.amazonaws.com" },
    ],
  },
};

export default nextConfig;

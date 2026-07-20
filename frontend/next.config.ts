import type { NextConfig } from "next";

const BACKEND_URL =
  process.env.BACKEND_URL || "https://ai-opportunity-scout-production.up.railway.app";

const nextConfig: NextConfig = {
  // Standalone output — optimal for Vercel and containerized deployments
  output: "standalone",

  // Proxy API calls through this domain so browsers never contact Railway
  // directly (single public URL; also dodges DNS/firewall issues with
  // *.railway.app on some networks).
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${BACKEND_URL}/api/:path*` },
      { source: "/health", destination: `${BACKEND_URL}/health` },
      { source: "/uploads/:path*", destination: `${BACKEND_URL}/uploads/:path*` },
    ];
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

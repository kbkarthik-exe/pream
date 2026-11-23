import type { NextConfig } from "next";

const backendUrl = process.env.BACKEND_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  /* Rewrites proxy /api/v1 requests to the Python FastAPI backend */
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
  experimental: {
    agentUpgrade: "security",
  },
};

export default nextConfig;

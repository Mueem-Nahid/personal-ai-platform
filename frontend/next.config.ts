import type { NextConfig } from "next";

const config: NextConfig = {
  async rewrites() {
    const api = process.env.BACKEND_URL ?? "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${api}/api/v1/:path*`,
      },
    ];
  },
};

export default config;

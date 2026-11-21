import type { NextConfig } from "next";

const apiBaseUrl = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
const apiUrl = new URL(apiBaseUrl);

if (
  apiUrl.protocol !== "http:" ||
  !["localhost", "127.0.0.1", "[::1]"].includes(apiUrl.hostname) ||
  apiUrl.username ||
  apiUrl.password
) {
  throw new Error("API_BASE_URL phải là địa chỉ HTTP localhost của FastAPI.");
}

const nextConfig: NextConfig = {
  poweredByHeader: false,
  distDir: process.env.NEXT_DIST_DIR ?? ".next",
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiBaseUrl.replace(/\/$/, "")}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;

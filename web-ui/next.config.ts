import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  async rewrites() {
    // Use runtime environment variable for API URL
    // Defaults to localhost:8001 for host networking mode
    // The web-api runs on port 8001 (internal HTTP) when using network_mode: host
    const apiUrl = process.env.BACKEND_API_URL || 'http://localhost:8001';

    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;

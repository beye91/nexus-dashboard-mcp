import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  async rewrites() {
    // Use runtime environment variable for API URL
    // This allows configuration without rebuilding
    const apiUrl = process.env.BACKEND_API_URL || 'http://web-api:8000';

    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;

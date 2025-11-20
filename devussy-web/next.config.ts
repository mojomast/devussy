import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
  async rewrites() {
    const useLocalApi = process.env.USE_LOCAL_API === 'true' || process.env.NODE_ENV === 'development';
    if (useLocalApi) {
      return [
        {
          source: '/api/:path*',
          destination: 'http://127.0.0.1:8000/api/:path*',
        },
      ];
    }
    // In production on Vercel, the API routes are hosted under /api and should not be proxied to localhost.
    return [];
  },
};

export default nextConfig;

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  typescript: {
    // TypeScript errors should be fixed, not ignored
    // Set to false to enforce type safety in builds
    ignoreBuildErrors: false,
  },
  eslint: {
    // ESLint errors should be fixed, not ignored
    ignoreDuringBuilds: false,
  },
  devIndicators: {
    position: 'bottom-right',
  },
  // Security headers
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ],
      },
    ];
  },
};

export default nextConfig;
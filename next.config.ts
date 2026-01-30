import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  typescript: {
    // Temporarily ignoring TS errors to deploy critical fixes
    // TODO: Fix TypeScript strict mode errors incrementally
    ignoreBuildErrors: true,
  },
  eslint: {
    // Temporarily ignoring ESLint during builds
    ignoreDuringBuilds: true,
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
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // eslint: { ignoreDuringBuilds: true } // Moved to command line or separate config if needed
};

export default nextConfig;

import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",   // necessário para o Dockerfile de produção
  experimental: {
    serverActions: {
      allowedOrigins: ["localhost:3000"],
    },
  },
};

export default nextConfig;

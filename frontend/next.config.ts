import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone", // necessário para o Dockerfile de produção
};

export default nextConfig;

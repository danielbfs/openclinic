/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone", // necessário para o Dockerfile de produção (Next.js 14+)
};

export default nextConfig;

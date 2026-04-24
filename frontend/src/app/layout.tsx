import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Open Clinic AI",
  description: "Sistema de gestão para clínicas com IA",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}

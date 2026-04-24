"use client";

import { AuthGuard } from "@/components/auth-guard";
import { AppHeader } from "@/components/app-header";

export default function SecretaryLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard allowedRoles={["admin", "secretary"]}>
      <div className="min-h-screen bg-gray-50">
        <AppHeader />
        {children}
      </div>
    </AuthGuard>
  );
}

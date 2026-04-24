"use client";

import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";

export function AppHeader() {
  const { user, logout } = useAuth();
  const router = useRouter();

  if (!user) return null;

  const roleLabel = user.role === "admin" ? "Administrador" : "Secretária";

  return (
    <header className="bg-white border-b px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <h1
          className="font-bold text-gray-900 cursor-pointer"
          onClick={() => router.push(user.role === "admin" ? "/admin" : "/secretary")}
        >
          Open Clinic AI
        </h1>
        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">
          {roleLabel}
        </span>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-600">{user.full_name}</span>
        <button
          onClick={() => router.push("/change-password")}
          className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
        >
          Alterar Senha
        </button>
        <button
          onClick={logout}
          className="text-sm text-red-500 hover:text-red-700 transition-colors"
        >
          Sair
        </button>
      </div>
    </header>
  );
}

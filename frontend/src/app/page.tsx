"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function Home() {
  const { user, isLoading, isAuthenticated, loadUser } = useAuth();
  const router = useRouter();

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  useEffect(() => {
    if (isLoading) return;

    if (isAuthenticated && user) {
      if (user.must_change_password) {
        router.replace("/change-password");
      } else if (user.role === "admin") {
        router.replace("/admin");
      } else {
        router.replace("/secretary");
      }
    }
  }, [isLoading, isAuthenticated, user, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-gray-400">Carregando...</div>
      </div>
    );
  }

  // Só mostra esta tela se NÃO estiver autenticado
  if (isAuthenticated) return null;

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Open Clinic AI
        </h1>
        <p className="text-gray-600 mb-8">
          Sistema open-source de gestão para clínicas
        </p>
        <a
          href="/login"
          className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Entrar
        </a>
      </div>
    </main>
  );
}

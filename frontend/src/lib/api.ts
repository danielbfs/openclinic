/**
 * Cliente HTTP para a API do Open Clinic AI.
 * Usa axios com interceptors para JWT automático.
 */
import axios from "axios";

// Em produção: URL relativa (mesmo domínio — Traefik roteia /api para o backend)
// Em dev: NEXT_PUBLIC_API_URL aponta para http://localhost:8000
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

// Adiciona token JWT automaticamente
api.interceptors.request.use((config) => {
  const token =
    typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Redireciona para login em 401 (exceto quando já está no login ou fazendo login)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      error.response?.status === 401 &&
      !error.config?.url?.includes("/auth/login") &&
      typeof window !== "undefined" &&
      !window.location.pathname.startsWith("/login")
    ) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

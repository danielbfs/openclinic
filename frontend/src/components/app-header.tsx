"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

interface Branding {
  name: string;
  logo_url: string;
}

const ADMIN_VIEWS = [
  { href: "/admin",     label: "Administração" },
  { href: "/secretary", label: "Secretaria"    },
  { href: "/doctor",    label: "Médico"        },
];

export function AppHeader() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [branding, setBranding] = useState<Branding>({ name: "Open Clinic AI", logo_url: "" });

  useEffect(() => {
    api.get("/admin/branding").then(({ data }) => setBranding(data)).catch(() => {});
  }, []);

  if (!user) return null;

  const roleLabel =
    user.role === "admin"     ? "Administrador" :
    user.role === "doctor"    ? "Médico"         :
                                "Secretária";

  const homeHref =
    user.role === "admin"  ? "/admin" :
    user.role === "doctor" ? "/doctor" :
                             "/secretary";

  const displayName = branding.name || "Open Clinic AI";

  return (
    <header className="bg-white border-b px-6 py-0 flex items-center justify-between h-16">
      {/* Logo + role badge */}
      <div className="flex items-center gap-3 shrink-0">
        <button
          onClick={() => router.push(homeHref)}
          className="flex items-center gap-2 hover:opacity-80 transition-opacity"
        >
          {branding.logo_url && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={branding.logo_url} alt={displayName} className="h-8 w-auto object-contain" />
          )}
          <span className="font-bold text-gray-900">{displayName}</span>
        </button>
        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">
          {roleLabel}
        </span>
      </div>

      {/* Admin view switcher — só para admin */}
      {user.role === "admin" && (
        <nav className="flex items-center h-full">
          {ADMIN_VIEWS.map(({ href, label }) => {
            const active = pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={`
                  h-full flex items-center px-4 text-sm font-medium border-b-2 transition-colors
                  ${active
                    ? "border-blue-600 text-blue-700"
                    : "border-transparent text-gray-500 hover:text-gray-800 hover:border-gray-300"}
                `}
              >
                {label}
              </Link>
            );
          })}
        </nav>
      )}

      {/* Ações do usuário */}
      <div className="flex items-center gap-4 shrink-0">
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

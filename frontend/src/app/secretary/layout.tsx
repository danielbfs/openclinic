"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AuthGuard } from "@/components/auth-guard";
import { AppHeader } from "@/components/app-header";

const NAV_ITEMS = [
  { href: "/secretary", label: "Leads" },
  { href: "/secretary/calendar", label: "Calendário" },
  { href: "/secretary/appointments", label: "Agendamentos" },
  { href: "/secretary/patients", label: "Pacientes" },
  { href: "/secretary/doctors", label: "Médicos" },
];

export default function SecretaryLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <AuthGuard allowedRoles={["admin", "secretary"]}>
      <div className="min-h-screen bg-gray-50">
        <AppHeader />
        <div className="flex">
          <nav className="w-52 bg-white border-r min-h-[calc(100vh-64px)] p-4 space-y-1">
            {NAV_ITEMS.map(({ href, label }) => {
              const active = href === "/secretary" ? pathname === "/secretary" : pathname.startsWith(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className={`block px-3 py-2 rounded-lg text-sm transition-colors ${
                    active
                      ? "bg-blue-50 text-blue-700 font-medium"
                      : "text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  {label}
                </Link>
              );
            })}
          </nav>
          <div className="flex-1">{children}</div>
        </div>
      </div>
    </AuthGuard>
  );
}

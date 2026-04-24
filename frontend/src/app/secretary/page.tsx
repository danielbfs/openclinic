"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Lead } from "@/types";

const STATUS_LABELS: Record<string, string> = {
  novo: "Novo",
  em_contato: "Em Contato",
  orcamento_enviado: "Orçamento Enviado",
  negociando: "Negociando",
  convertido: "Convertido",
  perdido: "Perdido",
};

const STATUS_COLORS: Record<string, string> = {
  novo: "bg-blue-100 text-blue-700",
  em_contato: "bg-yellow-100 text-yellow-700",
  orcamento_enviado: "bg-purple-100 text-purple-700",
  negociando: "bg-orange-100 text-orange-700",
  convertido: "bg-green-100 text-green-700",
  perdido: "bg-gray-100 text-gray-500",
};

export default function SecretaryPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLeads();
  }, [filter]);

  async function fetchLeads() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filter === "overdue") {
        params.set("is_overdue", "true");
      } else if (filter !== "all") {
        params.set("status", filter);
      }
      const { data } = await api.get(`/leads/?${params.toString()}`);
      setLeads(data);
    } catch {
      setLeads([]);
    } finally {
      setLoading(false);
    }
  }

  const overdueCnt = leads.filter((l) => l.is_overdue).length;

  return (
    <main className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Leads</h1>
        {overdueCnt > 0 && filter !== "overdue" && (
          <button
            onClick={() => setFilter("overdue")}
            className="text-sm bg-red-100 text-red-700 px-3 py-1 rounded-full font-medium"
          >
            {overdueCnt} vencido{overdueCnt > 1 ? "s" : ""}
          </button>
        )}
      </div>

      {/* Filtros */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {[
          { key: "all", label: "Todos" },
          { key: "novo", label: "Novos" },
          { key: "em_contato", label: "Em Contato" },
          { key: "orcamento_enviado", label: "Orçamento" },
          { key: "negociando", label: "Negociando" },
          { key: "overdue", label: "Vencidos" },
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`text-sm px-3 py-1.5 rounded-lg border transition-colors ${
              filter === key
                ? "bg-blue-600 text-white border-blue-600"
                : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Lista */}
      {loading ? (
        <p className="text-gray-400">Carregando...</p>
      ) : leads.length === 0 ? (
        <p className="text-gray-400">Nenhum lead encontrado.</p>
      ) : (
        <div className="bg-white border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Nome / Telefone</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Canal</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Status</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">SLA</th>
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Criado</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {leads.map((lead) => (
                <tr key={lead.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">{lead.full_name || "—"}</div>
                    <div className="text-gray-400">{lead.phone}</div>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{lead.channel}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[lead.status] || "bg-gray-100"}`}>
                      {STATUS_LABELS[lead.status] || lead.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {lead.is_overdue ? (
                      <span className="text-xs text-red-600 font-medium">VENCIDO</span>
                    ) : lead.contacted_at ? (
                      <span className="text-xs text-green-600">OK</span>
                    ) : (
                      <span className="text-xs text-gray-400">Aguardando</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {new Date(lead.created_at).toLocaleDateString("pt-BR")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}

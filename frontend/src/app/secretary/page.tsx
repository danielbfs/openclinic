"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
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

const CHANNEL_OPTIONS = [
  { value: "telegram", label: "Telegram" },
  { value: "whatsapp", label: "WhatsApp" },
  { value: "instagram", label: "Instagram" },
  { value: "site", label: "Site" },
  { value: "indicacao", label: "Indicação" },
  { value: "outro", label: "Outro" },
];

export default function SecretaryPage() {
  const router = useRouter();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({
    full_name: "",
    phone: "",
    email: "",
    channel: "whatsapp",
    description: "",
  });
  const [saving, setSaving] = useState(false);

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

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/leads/", {
        full_name: createForm.full_name || null,
        phone: createForm.phone,
        email: createForm.email || null,
        channel: createForm.channel,
        description: createForm.description || null,
      });
      setCreateForm({ full_name: "", phone: "", email: "", channel: "whatsapp", description: "" });
      setShowCreate(false);
      fetchLeads();
    } catch {
      alert("Erro ao criar lead.");
    } finally {
      setSaving(false);
    }
  }

  const overdueCnt = leads.filter((l) => l.is_overdue).length;

  return (
    <main className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Leads</h1>
        <div className="flex gap-2">
          {overdueCnt > 0 && filter !== "overdue" && (
            <button
              onClick={() => setFilter("overdue")}
              className="text-sm bg-red-100 text-red-700 px-3 py-1 rounded-full font-medium"
            >
              {overdueCnt} vencido{overdueCnt > 1 ? "s" : ""}
            </button>
          )}
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
          >
            {showCreate ? "Cancelar" : "Novo Lead"}
          </button>
        </div>
      </div>

      {/* Create Form */}
      {showCreate && (
        <form onSubmit={handleCreate} className="bg-white border rounded-lg p-4 mb-6 space-y-3">
          <h3 className="text-sm font-semibold text-gray-700">Novo Lead</h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-gray-500 mb-1">Nome</label>
              <input
                value={createForm.full_name}
                onChange={(e) => setCreateForm({ ...createForm, full_name: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm"
                placeholder="Nome do contato"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Telefone *</label>
              <input
                value={createForm.phone}
                onChange={(e) => setCreateForm({ ...createForm, phone: e.target.value })}
                required
                className="w-full border rounded-lg px-3 py-2 text-sm"
                placeholder="11999999999"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">E-mail</label>
              <input
                value={createForm.email}
                onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">Canal</label>
              <select
                value={createForm.channel}
                onChange={(e) => setCreateForm({ ...createForm, channel: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              >
                {CHANNEL_OPTIONS.map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div className="col-span-2">
              <label className="block text-xs text-gray-500 mb-1">Descrição / Queixa</label>
              <textarea
                value={createForm.description}
                onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm"
                rows={2}
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={saving}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "Salvando..." : "Criar Lead"}
          </button>
        </form>
      )}

      {/* Filters */}
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

      {/* Table */}
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
                <th className="text-left px-4 py-3 text-gray-500 font-medium">Ações</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {leads.map((lead) => (
                <tr
                  key={lead.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => router.push(`/secretary/leads/${lead.id}`)}
                >
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
                  <td className="px-4 py-3">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        router.push(`/secretary/leads/${lead.id}`);
                      }}
                      className="text-xs text-blue-600 hover:underline"
                    >
                      Ver detalhes
                    </button>
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

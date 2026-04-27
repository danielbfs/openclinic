"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

interface FollowupRule {
  id: string;
  name: string;
  trigger_event: string;
  offset_minutes: number;
  message_template: string;
  channel: string | null;
  is_active: boolean;
  created_at: string;
}

interface FollowupJob {
  id: string;
  rule_id: string;
  appointment_id: string;
  patient_id: string;
  scheduled_for: string;
  status: string;
  error_message: string | null;
  executed_at: string | null;
}

const TRIGGER_EVENTS = [
  { value: "appointment_scheduled", label: "Agendamento criado" },
  { value: "appointment_confirmed", label: "Agendamento confirmado" },
  { value: "appointment_cancelled", label: "Agendamento cancelado" },
  { value: "no_show", label: "Paciente faltou" },
];

const CHANNELS = [
  { value: "", label: "Mesmo canal do paciente" },
  { value: "telegram", label: "Telegram" },
  { value: "whatsapp", label: "WhatsApp" },
];

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  sent: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  cancelled: "bg-gray-100 text-gray-500",
};

export default function FollowUpsPage() {
  const [rules, setRules] = useState<FollowupRule[]>([]);
  const [jobs, setJobs] = useState<FollowupJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"rules" | "jobs">("rules");

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    trigger_event: "appointment_scheduled",
    offset_minutes: -1440,
    message_template: "",
    channel: "",
    is_active: true,
  });
  const [saving, setSaving] = useState(false);
  const templateRef = useRef<HTMLTextAreaElement>(null);

  // Jobs filter
  const [jobFilter, setJobFilter] = useState<string>("");

  useEffect(() => {
    fetchData();
  }, []);

  async function fetchData() {
    try {
      const [rulesRes, jobsRes] = await Promise.allSettled([
        api.get("/followup/rules"),
        api.get("/followup/jobs"),
      ]);
      if (rulesRes.status === "fulfilled") setRules(rulesRes.value.data);
      if (jobsRes.status === "fulfilled") setJobs(jobsRes.value.data);
    } finally {
      setLoading(false);
    }
  }

  async function fetchJobs(status?: string) {
    try {
      const params = status ? { status } : {};
      const { data } = await api.get("/followup/jobs", { params });
      setJobs(data);
    } catch {
      // ignore
    }
  }

  function openCreate() {
    setEditingId(null);
    setForm({
      name: "",
      trigger_event: "appointment_scheduled",
      offset_minutes: -1440,
      message_template:
        "Olá {patient_name}! Lembramos que sua consulta com {doctor_name} ({specialty}) está marcada para {appointment_date}. Confirme sua presença respondendo esta mensagem.",
      channel: "",
      is_active: true,
    });
    setShowForm(true);
  }

  function insertVariable(variable: string) {
    const el = templateRef.current;
    if (!el) {
      setForm((f) => ({ ...f, message_template: f.message_template + variable }));
      return;
    }
    const start = el.selectionStart ?? el.value.length;
    const end = el.selectionEnd ?? el.value.length;
    const newVal = el.value.slice(0, start) + variable + el.value.slice(end);
    setForm((f) => ({ ...f, message_template: newVal }));
    // Restore cursor after the inserted variable
    requestAnimationFrame(() => {
      el.focus();
      el.setSelectionRange(start + variable.length, start + variable.length);
    });
  }

  function openEdit(rule: FollowupRule) {
    setEditingId(rule.id);
    setForm({
      name: rule.name,
      trigger_event: rule.trigger_event,
      offset_minutes: rule.offset_minutes,
      message_template: rule.message_template,
      channel: rule.channel || "",
      is_active: rule.is_active,
    });
    setShowForm(true);
  }

  function cancelForm() {
    setShowForm(false);
    setEditingId(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        name: form.name,
        trigger_event: form.trigger_event,
        offset_minutes: form.offset_minutes,
        message_template: form.message_template,
        channel: form.channel || null,
        is_active: form.is_active,
      };
      if (editingId) {
        await api.patch(`/followup/rules/${editingId}`, payload);
      } else {
        await api.post("/followup/rules", payload);
      }
      cancelForm();
      fetchData();
    } catch {
      alert("Erro ao salvar regra de follow-up.");
    } finally {
      setSaving(false);
    }
  }

  async function toggleActive(rule: FollowupRule) {
    try {
      await api.patch(`/followup/rules/${rule.id}`, { is_active: !rule.is_active });
      fetchData();
    } catch {
      // ignore
    }
  }

  async function deleteRule(rule: FollowupRule) {
    if (!confirm(`Excluir regra "${rule.name}"?`)) return;
    try {
      await api.delete(`/followup/rules/${rule.id}`);
      fetchData();
    } catch {
      alert("Erro ao excluir regra.");
    }
  }

  function formatOffset(minutes: number): string {
    const abs = Math.abs(minutes);
    const direction = minutes < 0 ? "antes" : "depois";
    if (abs < 60) return `${abs} min ${direction}`;
    if (abs < 1440) return `${Math.round(abs / 60)}h ${direction}`;
    return `${Math.round(abs / 1440)}d ${direction}`;
  }

  function triggerLabel(event: string): string {
    return TRIGGER_EVENTS.find((e) => e.value === event)?.label || event;
  }

  if (loading) return <div className="p-8 text-gray-400">Carregando...</div>;

  return (
    <main className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Follow-ups</h1>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 border-b">
        <button
          onClick={() => setTab("rules")}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            tab === "rules"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          Regras
        </button>
        <button
          onClick={() => {
            setTab("jobs");
            fetchJobs(jobFilter || undefined);
          }}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            tab === "jobs"
              ? "border-blue-600 text-blue-600"
              : "border-transparent text-gray-500 hover:text-gray-700"
          }`}
        >
          Execuções
        </button>
      </div>

      {/* Rules Tab */}
      {tab === "rules" && (
        <>
          <div className="flex justify-end mb-4">
            <button
              onClick={showForm ? cancelForm : openCreate}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
            >
              {showForm ? "Cancelar" : "Nova Regra"}
            </button>
          </div>

          {showForm && (
            <form onSubmit={handleSubmit} className="bg-white border rounded-lg p-4 mb-6 space-y-3">
              <h3 className="text-sm font-semibold text-gray-700">
                {editingId ? "Editar Regra" : "Nova Regra de Follow-up"}
              </h3>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nome</label>
                  <input
                    value={form.name}
                    onChange={(e) => setForm({ ...form, name: e.target.value })}
                    required
                    placeholder="Ex: Lembrete 24h antes"
                    className="w-full border rounded-lg px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Evento gatilho</label>
                  <select
                    value={form.trigger_event}
                    onChange={(e) => setForm({ ...form, trigger_event: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2 text-sm"
                  >
                    {TRIGGER_EVENTS.map((te) => (
                      <option key={te.value} value={te.value}>
                        {te.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Offset (minutos)
                  </label>
                  <input
                    type="number"
                    value={form.offset_minutes}
                    onChange={(e) => setForm({ ...form, offset_minutes: Number(e.target.value) })}
                    className="w-full border rounded-lg px-3 py-2 text-sm"
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Negativo = antes do evento. Ex: -1440 = 24h antes, 60 = 1h depois
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Canal de envio</label>
                  <select
                    value={form.channel}
                    onChange={(e) => setForm({ ...form, channel: e.target.value })}
                    className="w-full border rounded-lg px-3 py-2 text-sm"
                  >
                    {CHANNELS.map((ch) => (
                      <option key={ch.value} value={ch.value}>
                        {ch.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-sm font-medium text-gray-700">
                    Template da mensagem
                  </label>
                  <span className="text-xs text-gray-400">Clique numa variável para inserir no cursor</span>
                </div>
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {[
                    { tag: "{patient_name}",    label: "Nome do paciente"    },
                    { tag: "{doctor_name}",     label: "Nome do médico"      },
                    { tag: "{specialty}",       label: "Especialidade"       },
                    { tag: "{appointment_date}", label: "Data/hora consulta" },
                  ].map(({ tag, label }) => (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => insertVariable(tag)}
                      className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs rounded-md border border-blue-200 transition-colors font-mono"
                      title={label}
                    >
                      {tag}
                    </button>
                  ))}
                </div>
                <textarea
                  ref={templateRef}
                  value={form.message_template}
                  onChange={(e) => setForm({ ...form, message_template: e.target.value })}
                  required
                  rows={4}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                  placeholder="Ex: Olá {patient_name}! Sua consulta com {doctor_name} ({specialty}) está marcada para {appointment_date}."
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                  id="is_active"
                  className="rounded"
                />
                <label htmlFor="is_active" className="text-sm text-gray-700">
                  Regra ativa
                </label>
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  {saving ? "Salvando..." : editingId ? "Salvar" : "Criar"}
                </button>
                <button type="button" onClick={cancelForm} className="text-sm text-gray-500 px-4 py-2">
                  Cancelar
                </button>
              </div>
            </form>
          )}

          <div className="bg-white border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 text-gray-500 font-medium">Nome</th>
                  <th className="text-left px-4 py-3 text-gray-500 font-medium">Evento</th>
                  <th className="text-left px-4 py-3 text-gray-500 font-medium">Offset</th>
                  <th className="text-left px-4 py-3 text-gray-500 font-medium">Canal</th>
                  <th className="text-left px-4 py-3 text-gray-500 font-medium">Status</th>
                  <th className="text-left px-4 py-3 text-gray-500 font-medium">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {rules.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                      Nenhuma regra de follow-up cadastrada.
                    </td>
                  </tr>
                ) : (
                  rules.map((rule) => (
                    <tr key={rule.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium text-gray-900">{rule.name}</td>
                      <td className="px-4 py-3 text-gray-500">{triggerLabel(rule.trigger_event)}</td>
                      <td className="px-4 py-3 text-gray-500">{formatOffset(rule.offset_minutes)}</td>
                      <td className="px-4 py-3 text-gray-500">{rule.channel || "Paciente"}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                            rule.is_active
                              ? "bg-green-100 text-green-700"
                              : "bg-gray-100 text-gray-500"
                          }`}
                        >
                          {rule.is_active ? "Ativa" : "Inativa"}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-3">
                          <button
                            onClick={() => openEdit(rule)}
                            className="text-xs text-blue-600 hover:underline"
                          >
                            Editar
                          </button>
                          <button
                            onClick={() => toggleActive(rule)}
                            className="text-xs text-yellow-600 hover:underline"
                          >
                            {rule.is_active ? "Desativar" : "Ativar"}
                          </button>
                          <button
                            onClick={() => deleteRule(rule)}
                            className="text-xs text-red-600 hover:underline"
                          >
                            Excluir
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Jobs Tab */}
      {tab === "jobs" && (
        <>
          <div className="flex gap-2 mb-4">
            {["", "pending", "sent", "failed", "cancelled"].map((s) => (
              <button
                key={s}
                onClick={() => {
                  setJobFilter(s);
                  fetchJobs(s || undefined);
                }}
                className={`px-3 py-1.5 text-xs rounded-full font-medium border transition-colors ${
                  jobFilter === s
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
                }`}
              >
                {s === "" ? "Todos" : s === "pending" ? "Pendentes" : s === "sent" ? "Enviados" : s === "failed" ? "Falhas" : "Cancelados"}
              </button>
            ))}
          </div>

          <div className="bg-white border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left px-4 py-3 text-gray-500 font-medium">Agendado para</th>
                  <th className="text-left px-4 py-3 text-gray-500 font-medium">Status</th>
                  <th className="text-left px-4 py-3 text-gray-500 font-medium">Executado em</th>
                  <th className="text-left px-4 py-3 text-gray-500 font-medium">Erro</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {jobs.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                      Nenhuma execução encontrada.
                    </td>
                  </tr>
                ) : (
                  jobs.map((job) => (
                    <tr key={job.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-gray-900">
                        {new Date(job.scheduled_for).toLocaleString("pt-BR")}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                            STATUS_COLORS[job.status] || "bg-gray-100 text-gray-500"
                          }`}
                        >
                          {job.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {job.executed_at
                          ? new Date(job.executed_at).toLocaleString("pt-BR")
                          : "—"}
                      </td>
                      <td className="px-4 py-3 text-gray-500 text-xs max-w-xs truncate">
                        {job.error_message || "—"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </main>
  );
}

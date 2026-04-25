"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface SetupStatus {
  telegram_configured: boolean;
  openai_configured: boolean;
  local_llm_configured: boolean;
  domain: string;
}

interface ClinicSettings {
  name: string;
  timezone: string;
  phone: string;
  address: string;
}

interface SLASettings {
  hours: number;
}

interface AISettings {
  type: string;
  model: string;
}

const TIMEZONES = [
  "America/Sao_Paulo",
  "America/Fortaleza",
  "America/Manaus",
  "America/Rio_Branco",
  "America/Bahia",
  "America/Belem",
  "America/Cuiaba",
  "America/Recife",
];

const AI_MODELS = [
  { value: "gpt-4o", label: "GPT-4o" },
  { value: "gpt-4o-mini", label: "GPT-4o Mini (recomendado)" },
  { value: "gpt-4-turbo", label: "GPT-4 Turbo" },
  { value: "local", label: "LLM Local (Ollama)" },
];

export default function SetupPage() {
  const [status, setStatus] = useState<SetupStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [webhookResult, setWebhookResult] = useState<string | null>(null);
  const [settingWebhook, setSettingWebhook] = useState(false);

  // Settings forms
  const [clinic, setClinic] = useState<ClinicSettings>({
    name: "",
    timezone: "America/Sao_Paulo",
    phone: "",
    address: "",
  });
  const [sla, setSla] = useState<SLASettings>({ hours: 2 });
  const [ai, setAi] = useState<AISettings>({ type: "openai", model: "gpt-4o-mini" });

  const [savingClinic, setSavingClinic] = useState(false);
  const [savingSla, setSavingSla] = useState(false);
  const [savingAi, setSavingAi] = useState(false);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);

  useEffect(() => {
    fetchAll();
  }, []);

  async function fetchAll() {
    try {
      const [statusRes, settingsRes] = await Promise.allSettled([
        api.get("/admin/setup/status"),
        api.get("/admin/settings"),
      ]);
      if (statusRes.status === "fulfilled") setStatus(statusRes.value.data);
      if (settingsRes.status === "fulfilled") {
        const s = settingsRes.value.data;
        setClinic(s.clinic);
        setSla(s.sla);
        setAi(s.ai);
      }
    } finally {
      setLoading(false);
    }
  }

  function showSaved(msg: string) {
    setSavedMsg(msg);
    setTimeout(() => setSavedMsg(null), 3000);
  }

  async function saveClinic() {
    setSavingClinic(true);
    try {
      await api.patch("/admin/settings/clinic", clinic);
      showSaved("Dados da clínica salvos.");
    } catch {
      alert("Erro ao salvar.");
    } finally {
      setSavingClinic(false);
    }
  }

  async function saveSla() {
    setSavingSla(true);
    try {
      await api.patch("/admin/settings/sla", sla);
      showSaved("SLA atualizado.");
    } catch {
      alert("Erro ao salvar.");
    } finally {
      setSavingSla(false);
    }
  }

  async function saveAi() {
    setSavingAi(true);
    try {
      await api.patch("/admin/settings/ai", ai);
      showSaved("Configuração de IA salva.");
    } catch {
      alert("Erro ao salvar.");
    } finally {
      setSavingAi(false);
    }
  }

  async function setupTelegramWebhook() {
    setSettingWebhook(true);
    setWebhookResult(null);
    try {
      const { data } = await api.post("/admin/setup/telegram-webhook");
      if (data.success) {
        setWebhookResult(`Webhook registrado: ${data.webhook_url}`);
      } else {
        setWebhookResult("Falha ao registrar webhook. Verifique o TELEGRAM_BOT_TOKEN.");
      }
    } catch {
      setWebhookResult("Erro ao conectar com o servidor.");
    } finally {
      setSettingWebhook(false);
    }
  }

  if (loading) return <div className="p-8 text-gray-400">Carregando...</div>;

  return (
    <main className="p-8 max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Setup da Clínica</h1>

      {savedMsg && (
        <div className="mb-4 bg-green-50 border border-green-200 text-green-700 text-sm px-4 py-2 rounded-lg">
          {savedMsg}
        </div>
      )}

      <div className="space-y-6">
        {/* Clinic Info */}
        <div className="bg-white border rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Dados da Clínica</h2>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nome da Clínica
              </label>
              <input
                value={clinic.name}
                onChange={(e) => setClinic({ ...clinic, name: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Fuso horário</label>
              <select
                value={clinic.timezone}
                onChange={(e) => setClinic({ ...clinic, timezone: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              >
                {TIMEZONES.map((tz) => (
                  <option key={tz} value={tz}>
                    {tz}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Telefone</label>
              <input
                value={clinic.phone}
                onChange={(e) => setClinic({ ...clinic, phone: e.target.value })}
                placeholder="(11) 99999-9999"
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Endereço</label>
              <input
                value={clinic.address}
                onChange={(e) => setClinic({ ...clinic, address: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              />
            </div>
          </div>
          <button
            onClick={saveClinic}
            disabled={savingClinic}
            className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {savingClinic ? "Salvando..." : "Salvar Dados da Clínica"}
          </button>
        </div>

        {/* SLA */}
        <div className="bg-white border rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">SLA de Leads</h2>
          <p className="text-sm text-gray-500 mb-4">
            Tempo máximo para a equipe realizar o primeiro contato com um novo lead.
          </p>
          <div className="flex items-center gap-3">
            <input
              type="number"
              value={sla.hours}
              onChange={(e) => setSla({ hours: Number(e.target.value) })}
              min={1}
              max={72}
              className="w-24 border rounded-lg px-3 py-2 text-sm"
            />
            <span className="text-sm text-gray-600">horas</span>
            <button
              onClick={saveSla}
              disabled={savingSla}
              className="ml-4 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {savingSla ? "Salvando..." : "Salvar SLA"}
            </button>
          </div>
        </div>

        {/* AI Configuration */}
        <div className="bg-white border rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Inteligência Artificial</h2>
          <p className="text-sm text-gray-500 mb-4">
            Modelo de IA usado pelo assistente virtual para conversar com os pacientes.
          </p>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Provedor</label>
              <select
                value={ai.type}
                onChange={(e) => setAi({ ...ai, type: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              >
                <option value="openai">OpenAI</option>
                <option value="local">LLM Local (Ollama)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Modelo</label>
              <select
                value={ai.model}
                onChange={(e) => setAi({ ...ai, model: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              >
                {AI_MODELS.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <button
            onClick={saveAi}
            disabled={savingAi}
            className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {savingAi ? "Salvando..." : "Salvar Configuração de IA"}
          </button>
        </div>

        {/* Integration Status */}
        <div className="bg-white border rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Status das Integrações</h2>
          <div className="space-y-3">
            <StatusRow label="Domínio" value={status?.domain || "—"} ok={!!status?.domain} />
            <StatusRow
              label="Telegram Bot"
              value={status?.telegram_configured ? "Configurado" : "Não configurado"}
              ok={!!status?.telegram_configured}
            />
            <StatusRow
              label="OpenAI"
              value={status?.openai_configured ? "Configurado" : "Não configurado"}
              ok={!!status?.openai_configured}
            />
            <StatusRow
              label="LLM Local"
              value={status?.local_llm_configured ? "Configurado" : "Não configurado"}
              ok={!!status?.local_llm_configured}
            />
          </div>
        </div>

        {/* Telegram Webhook */}
        {status?.telegram_configured && (
          <div className="bg-white border rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">Telegram Webhook</h2>
            <p className="text-sm text-gray-500 mb-4">
              Registre o webhook para que o bot Telegram receba mensagens dos pacientes.
            </p>
            <button
              onClick={setupTelegramWebhook}
              disabled={settingWebhook}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {settingWebhook ? "Registrando..." : "Registrar Webhook Telegram"}
            </button>
            {webhookResult && (
              <p className="mt-3 text-sm text-gray-600">{webhookResult}</p>
            )}
          </div>
        )}

        {/* Instructions */}
        <div className="bg-gray-50 border rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Como configurar</h2>
          <ol className="text-sm text-gray-600 space-y-2 list-decimal list-inside">
            <li>
              Configure as variáveis de ambiente no arquivo{" "}
              <code className="bg-gray-200 px-1 rounded">.env</code>
            </li>
            <li>
              Reinicie os containers:{" "}
              <code className="bg-gray-200 px-1 rounded">docker compose up -d</code>
            </li>
            <li>Preencha os dados da clínica acima e salve</li>
            <li>Registre o webhook do Telegram (se configurado)</li>
            <li>Teste enviando uma mensagem para o bot no Telegram</li>
          </ol>
        </div>
      </div>
    </main>
  );
}

function StatusRow({ label, value, ok }: { label: string; value: string; ok: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-gray-600">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-gray-900">{value}</span>
        <span className={`w-2.5 h-2.5 rounded-full ${ok ? "bg-green-500" : "bg-gray-300"}`} />
      </div>
    </div>
  );
}

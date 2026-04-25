"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface SetupStatus {
  telegram_configured: boolean;
  openai_configured: boolean;
  local_llm_configured: boolean;
  domain: string;
}

export default function SetupPage() {
  const [status, setStatus] = useState<SetupStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [webhookResult, setWebhookResult] = useState<string | null>(null);
  const [settingWebhook, setSettingWebhook] = useState(false);

  useEffect(() => {
    fetchStatus();
  }, []);

  async function fetchStatus() {
    try {
      const { data } = await api.get("/admin/setup/status");
      setStatus(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
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

  if (loading) {
    return <div className="p-8 text-gray-400">Carregando...</div>;
  }

  return (
    <main className="p-8 max-w-2xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Setup da Clínica</h1>

      <div className="space-y-6">
        {/* Status das integrações */}
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
            <li>Configure as variáveis de ambiente no arquivo <code className="bg-gray-200 px-1 rounded">.env</code></li>
            <li>Reinicie os containers: <code className="bg-gray-200 px-1 rounded">docker compose up -d</code></li>
            <li>Retorne a esta página e registre o webhook do Telegram</li>
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

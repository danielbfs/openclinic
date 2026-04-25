"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface AISettings {
  type: string;
  model: string;
  use_local_llm: boolean;
  local_llm_url: string;
  local_llm_model: string;
}

interface ChatbotSettings {
  system_prompt: string;
  max_tool_calls: number;
  temperature: number;
}

const OPENAI_MODELS = [
  { value: "gpt-4o", label: "GPT-4o (mais capaz)" },
  { value: "gpt-4o-mini", label: "GPT-4o Mini (custo-benefício)" },
  { value: "gpt-4-turbo", label: "GPT-4 Turbo" },
];

const LOCAL_MODELS = [
  { value: "llama3.2", label: "Llama 3.2" },
  { value: "llama3.1", label: "Llama 3.1" },
  { value: "mistral", label: "Mistral" },
  { value: "gemma2", label: "Gemma 2" },
];

const DEFAULT_PROMPT = `Suas responsabilidades:
1. Atender pacientes com cordialidade e profissionalismo
2. Verificar disponibilidade e agendar consultas
3. Confirmar, cancelar ou remarcar consultas existentes
4. Coletar informações básicas (nome, queixa principal)
5. Responder dúvidas gerais sobre a clínica

Regras IMPORTANTES:
- NUNCA invente horários. Use SEMPRE a ferramenta check_availability para consultar disponibilidade real
- Se o paciente quiser agendar, pergunte a especialidade ou médico desejado e a data de preferência
- Ao oferecer horários, apresente no máximo 5 opções de forma clara
- Antes de confirmar um agendamento, SEMPRE pergunte ao paciente se o horário está ok
- Se o paciente fizer perguntas médicas, oriente-o a consultar o médico
- Se não conseguir resolver algo, use escalate_to_human para transferir à secretária
- Fale em português do Brasil, com tom profissional mas acolhedor
- Seja conciso — mensagens curtas e diretas são melhores em chat
- Formate datas como "segunda-feira, 28 de abril às 14:00"`;

export default function ChatbotPage() {
  const [loading, setLoading] = useState(true);
  const [ai, setAi] = useState<AISettings>({
    type: "openai",
    model: "gpt-4o-mini",
    use_local_llm: false,
    local_llm_url: "",
    local_llm_model: "",
  });
  const [chatbot, setChatbot] = useState<ChatbotSettings>({
    system_prompt: "",
    max_tool_calls: 3,
    temperature: 0.3,
  });
  const [savingAi, setSavingAi] = useState(false);
  const [savingChatbot, setSavingChatbot] = useState(false);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  async function fetchSettings() {
    try {
      const { data } = await api.get("/admin/settings");
      setAi(data.ai);
      setChatbot(data.chatbot);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  function showSaved(msg: string) {
    setSavedMsg(msg);
    setTimeout(() => setSavedMsg(null), 3000);
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

  async function saveChatbot() {
    setSavingChatbot(true);
    try {
      await api.patch("/admin/settings/chatbot", chatbot);
      showSaved("Prompt do chatbot salvo.");
    } catch {
      alert("Erro ao salvar.");
    } finally {
      setSavingChatbot(false);
    }
  }

  function resetPrompt() {
    setChatbot({ ...chatbot, system_prompt: "" });
  }

  if (loading) return <div className="p-8 text-gray-400">Carregando...</div>;

  return (
    <main className="p-8 max-w-3xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Chatbot / Assistente IA</h1>

      {savedMsg && (
        <div className="mb-4 bg-green-50 border border-green-200 text-green-700 text-sm px-4 py-2 rounded-lg">
          {savedMsg}
        </div>
      )}

      <div className="space-y-6">
        {/* AI Provider */}
        <div className="bg-white border rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Provedor de IA</h2>
          <p className="text-sm text-gray-500 mb-4">
            Escolha qual serviço de IA o chatbot usará para conversar com os pacientes.
          </p>

          {/* Toggle LLM local */}
          <div className="flex items-center gap-3 mb-4 p-3 bg-gray-50 rounded-lg">
            <input
              type="checkbox"
              checked={ai.use_local_llm}
              onChange={(e) =>
                setAi({
                  ...ai,
                  use_local_llm: e.target.checked,
                  type: e.target.checked ? "local" : "openai",
                })
              }
              id="use_local"
              className="rounded"
            />
            <label htmlFor="use_local" className="text-sm text-gray-700">
              <span className="font-medium">Usar LLM Local (Ollama)</span>
              <span className="block text-xs text-gray-500">
                Requer VPS com 8+ vCPU e 16GB RAM. Sem custo de API, mas mais lento.
              </span>
            </label>
          </div>

          {ai.use_local_llm ? (
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  URL do Ollama
                </label>
                <input
                  value={ai.local_llm_url}
                  onChange={(e) => setAi({ ...ai, local_llm_url: e.target.value })}
                  placeholder="http://ollama:11434/v1"
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Se Ollama está no mesmo Docker Compose, use http://ollama:11434/v1
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Modelo</label>
                <select
                  value={ai.local_llm_model}
                  onChange={(e) => setAi({ ...ai, local_llm_model: e.target.value })}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                >
                  <option value="">Selecione...</option>
                  {LOCAL_MODELS.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-400 mt-1">
                  Ou digite o nome do modelo se não estiver na lista
                </p>
                <input
                  value={ai.local_llm_model}
                  onChange={(e) => setAi({ ...ai, local_llm_model: e.target.value })}
                  placeholder="nome-do-modelo"
                  className="w-full border rounded-lg px-3 py-2 text-sm mt-1"
                />
              </div>
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Modelo OpenAI</label>
              <select
                value={ai.model}
                onChange={(e) => setAi({ ...ai, model: e.target.value })}
                className="w-full border rounded-lg px-3 py-2 text-sm"
              >
                {OPENAI_MODELS.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-400 mt-1">
                A API key é configurada no .env (OPENAI_API_KEY). O modelo selecionado aqui é usado pelo chatbot.
              </p>
            </div>
          )}

          <button
            onClick={saveAi}
            disabled={savingAi}
            className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {savingAi ? "Salvando..." : "Salvar Configuração de IA"}
          </button>
        </div>

        {/* Chatbot Behavior */}
        <div className="bg-white border rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            Comportamento do Chatbot
          </h2>
          <p className="text-sm text-gray-500 mb-4">
            Personalize como o assistente virtual se comporta nas conversas com pacientes.
          </p>

          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-sm font-medium text-gray-700">
                  Instruções do Chatbot (System Prompt)
                </label>
                <button
                  onClick={resetPrompt}
                  className="text-xs text-blue-600 hover:underline"
                >
                  Restaurar padrão
                </button>
              </div>
              <textarea
                value={chatbot.system_prompt || ""}
                onChange={(e) => setChatbot({ ...chatbot, system_prompt: e.target.value })}
                rows={14}
                className="w-full border rounded-lg px-3 py-2 text-sm font-mono"
                placeholder={DEFAULT_PROMPT}
              />
              <p className="text-xs text-gray-400 mt-1">
                Deixe vazio para usar o prompt padrão. Edite para personalizar o tom, regras
                especiais da sua clínica, ou instruções adicionais.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Temperatura
                </label>
                <input
                  type="number"
                  value={chatbot.temperature}
                  onChange={(e) =>
                    setChatbot({ ...chatbot, temperature: Number(e.target.value) })
                  }
                  min={0}
                  max={1}
                  step={0.1}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                />
                <p className="text-xs text-gray-400 mt-1">
                  0 = mais preciso, 1 = mais criativo. Recomendado: 0.3
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Tool Calls
                </label>
                <input
                  type="number"
                  value={chatbot.max_tool_calls}
                  onChange={(e) =>
                    setChatbot({ ...chatbot, max_tool_calls: Number(e.target.value) })
                  }
                  min={1}
                  max={10}
                  className="w-full border rounded-lg px-3 py-2 text-sm"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Limite de ações por mensagem (agendar, verificar, etc.)
                </p>
              </div>
            </div>
          </div>

          <button
            onClick={saveChatbot}
            disabled={savingChatbot}
            className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {savingChatbot ? "Salvando..." : "Salvar Comportamento"}
          </button>
        </div>

        {/* Preview */}
        <div className="bg-gray-50 border rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Resumo Ativo</h2>
          <div className="text-sm text-gray-600 space-y-1">
            <p>
              <span className="font-medium">Provedor:</span>{" "}
              {ai.use_local_llm ? "LLM Local (Ollama)" : "OpenAI"}
            </p>
            <p>
              <span className="font-medium">Modelo:</span>{" "}
              {ai.use_local_llm ? ai.local_llm_model || "não definido" : ai.model}
            </p>
            {ai.use_local_llm && (
              <p>
                <span className="font-medium">URL:</span>{" "}
                {ai.local_llm_url || "não definido"}
              </p>
            )}
            <p>
              <span className="font-medium">Temperatura:</span> {chatbot.temperature}
            </p>
            <p>
              <span className="font-medium">Prompt personalizado:</span>{" "}
              {chatbot.system_prompt ? "Sim" : "Usando padrão"}
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}

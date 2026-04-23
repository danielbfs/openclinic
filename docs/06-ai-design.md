---
tags: [openclinic, ai, llm]
created: 2026-04-23
status: draft
---

# AI Engine — Open Clinic AI

## Responsabilidades

1. Gerenciar sessão de conversa (histórico por paciente)
2. Montar contexto para o LLM (system prompt + histórico + mensagem)
3. Executar function calling (tools de agendamento)
4. Abstrair o provider de LLM (OpenAI ou Local)

---

## Fluxo de Processamento

```
MessagePayload recebida
  │
  ├── ai/session.py
  │     Carrega histórico do Redis (key: session:{patient_id})
  │     Se expirou (>24h): busca últimas 5 mensagens do DB
  │
  ├── ai/engine.py
  │     Monta: system_prompt + histórico + nova mensagem
  │
  ├── LLM Adapter
  │     Envia para OpenAI ou Local LLM
  │
  ├── Resposta do LLM
  │     ┌── tool_call? ──────────────────────────────────────┐
  │     │   ai/tools.py executa a tool                        │
  │     │   Adiciona resultado ao contexto                    │
  │     │   Reenvia para LLM (loop até max 3 tool calls)      │
  │     └────────────────────────────────────────────────────┘
  │     └── text: resposta final
  │
  ├── Salva mensagem + resposta
  │     → Redis (TTL 24h) + PostgreSQL
  │
  └── Retorna resposta para MessagingGateway
```

---

## Tools (Function Calling)

```python
TOOLS = [
    {
        "name": "check_availability",
        "description": "Verifica horários disponíveis para agendamento",
        "parameters": {
            "type": "object",
            "properties": {
                "specialty_id": {
                    "type": "string",
                    "description": "UUID da especialidade desejada"
                },
                "date_from": {
                    "type": "string",
                    "description": "Data início no formato ISO 8601"
                },
                "date_to": {
                    "type": "string",
                    "description": "Data fim no formato ISO 8601"
                }
            },
            "required": ["specialty_id", "date_from", "date_to"]
        }
    },
    {
        "name": "book_appointment",
        "description": "Agenda uma consulta para o paciente atual",
        "parameters": {
            "type": "object",
            "properties": {
                "doctor_id": {"type": "string"},
                "starts_at": {"type": "string", "description": "ISO 8601"},
                "patient_notes": {"type": "string"}
            },
            "required": ["doctor_id", "starts_at"]
        }
    },
    {
        "name": "cancel_appointment",
        "description": "Cancela uma consulta agendada",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {"type": "string"}
            },
            "required": ["appointment_id"]
        }
    },
    {
        "name": "reschedule_appointment",
        "description": "Remarca uma consulta para outro horário",
        "parameters": {
            "type": "object",
            "properties": {
                "appointment_id": {"type": "string"},
                "new_starts_at": {"type": "string", "description": "ISO 8601"}
            },
            "required": ["appointment_id", "new_starts_at"]
        }
    },
    {
        "name": "get_patient_appointments",
        "description": "Lista as consultas agendadas do paciente atual",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "escalate_to_human",
        "description": "Transfere a conversa para atendimento humano",
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Motivo da transferência"
                }
            },
            "required": ["reason"]
        }
    }
]
```

---

## System Prompt Base

```
Você é o assistente virtual da {CLINIC_NAME}.

Data e hora atual: {current_datetime} (fuso: {CLINIC_TIMEZONE})

Especialidades disponíveis:
{specialties_list}

Suas responsabilidades:
1. Atender pacientes com cordialidade e profissionalismo
2. Verificar disponibilidade e agendar consultas
3. Confirmar, cancelar ou remarcar consultas existentes
4. Coletar nome e motivo da consulta quando não informados

Regras OBRIGATÓRIAS:
- NUNCA invente ou confirme horários sem usar a tool check_availability
- Quando o paciente quiser agendar: use check_availability PRIMEIRO
- Se não conseguir resolver: use escalate_to_human
- Não responda perguntas médicas — oriente a consultar um profissional
- Fale em português do Brasil, tom acolhedor e profissional
- Mensagens curtas e objetivas (máximo 3 parágrafos)
```

---

## LLM Adapters

### OpenAIAdapter
```python
class OpenAIAdapter(AbstractLLMAdapter):
    def __init__(self, model: str, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model  # gpt-4o-mini padrão

    async def complete(self, messages, tools) -> LLMResponse:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        return LLMResponse.from_openai(response)
```

### LocalLLMAdapter
```python
class LocalLLMAdapter(AbstractLLMAdapter):
    def __init__(self, base_url: str, model: str):
        # Compatível com qualquer endpoint OpenAI-compatible
        # Testado com: Ollama, LM Studio, vLLM
        self.client = AsyncOpenAI(base_url=base_url, api_key="local")
        self.model = model  # ex: llama3.2, mistral:7b

    async def complete(self, messages, tools) -> LLMResponse:
        # Mesma interface do OpenAI
        ...
```

---

## Gerenciamento de Sessão

```
Redis key: session:{patient_id}
TTL: 86400 segundos (24 horas)
Estrutura: JSON list de messages [{role, content}, ...]

Limite de contexto:
- Máximo 20 mensagens na sessão Redis
- Ao atingir limite: gera context_summary via LLM e trunca
- Fallback (sessão expirada): carrega últimas 5 mensagens do DB
```

---

## Configuração via Admin

O provider de LLM é configurado via wizard e salvo em `system_config`:

```json
// key: "ai_provider"
{
  "type": "openai",
  "model": "gpt-4o-mini",
  "api_key_ref": "env:OPENAI_API_KEY"
}

// ou para Local LLM
{
  "type": "local_llm",
  "base_url": "http://ollama:11434/v1",
  "model": "llama3.2"
}
```

`api_key_ref` usa o padrão `env:NOME_VAR` para nunca salvar secrets no banco.

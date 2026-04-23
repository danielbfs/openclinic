---
tags: [openclinic, architecture]
created: 2026-04-23
status: draft
---

# Arquitetura — Open Clinic AI

## Decisões de Stack

### Backend: FastAPI (Python 3.12)
- Ecossistema AI nativo (OpenAI SDK, Ollama, LangChain)
- `async/await` nativo — essencial para webhooks e filas
- Pydantic v2 para validação e schemas tipados
- OpenAPI auto-gerado (docs sempre atualizados)
- Celery integrado naturalmente

### Frontend: Next.js 14 + TypeScript
- App Router com React Server Components
- Shadcn/ui + TailwindCSS
- Roles: `admin` e `secretary` com rotas protegidas

### Infra
- **PostgreSQL 16** — dados primários
- **Redis 7** — fila Celery + cache de sessão de conversa (TTL 24h)
- **Celery** — workers assíncronos + beat scheduler
- **Traefik v3** — reverse proxy + SSL automático via Let's Encrypt
- **Docker + Docker Compose** — deploy em VPS

---

## Diagrama de Alto Nível

```
┌──────────────────────────────────────────────────────────────────┐
│                        CLIENTES EXTERNOS                          │
│   Paciente                    Admin / Secretária                  │
│ [Telegram] [WhatsApp]         [Browser → Next.js]                │
└──────┬──────────┬──────────────────────┬───────────────────────┘
       │          │                      │
       ▼          ▼                      ▼
┌──────────────────────┐      ┌────────────────────────────────────┐
│  MESSAGING GATEWAY    │      │      Traefik (Reverse Proxy)       │
│  Telegram / WA       │      │  :80 → redirect :443               │
│  Adapters            │      │  :443 → backend /api + /webhooks   │
└──────────┬───────────┘      │         frontend /                 │
           │                  └────────────────────────────────────┘
           ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (port 8000)                    │
│                                                                   │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────────────┐   │
│  │ Messaging  │  │ AI Engine  │  │    SchedulingService      │   │
│  │  Module    │→ │  Module    │→ │  (Abstraction Layer)      │   │
│  └────────────┘  └────────────┘  │  ┌────────┐ ┌─────────┐ │   │
│                                  │  │ GCal   │ │ LocalDB │ │   │
│  ┌────────────┐  ┌────────────┐  │  │ Adapter│ │ Adapter │ │   │
│  │    CRM     │  │  Leads     │  │  └────────┘ └─────────┘ │   │
│  │   Module   │  │  Module    │  └──────────────────────────┘   │
│  └────────────┘  └────────────┘                                  │
│                                  ┌──────────────────────────┐   │
│  ┌────────────┐  ┌────────────┐  │   Auth + Audit Module    │   │
│  │  Follow-up │  │  Reports   │  │   JWT + RBAC + Logs      │   │
│  │   Module   │  │   Module   │  └──────────────────────────┘   │
│  └────────────┘  └────────────┘                                  │
└──────────────────────────────┬───────────────────────────────────┘
                               │
           ┌───────────────────┼────────────────────┐
           ▼                   ▼                    ▼
   ┌──────────────┐   ┌──────────────┐   ┌───────────────────────┐
   │ PostgreSQL   │   │    Redis     │   │   APIs Externas        │
   │  (port 5432) │   │  Queue+Cache │   │   Google Calendar      │
   └──────────────┘   └──────────────┘   │   OpenAI / Local LLM  │
                               │          │   Meta Ads / Google Ads│
                     ┌─────────┴───────┐  └───────────────────────┘
                     ▼                 ▼
             ┌─────────────┐  ┌──────────────┐
             │Celery Worker│  │ Celery Beat  │
             │ (followup,  │  │ (cron tasks) │
             │  leads SLA) │  └──────────────┘
             └─────────────┘
```

---

## Fluxo Principal: Paciente → Agendamento

```
[Paciente envia mensagem no Telegram]
  → Webhook POST /api/v1/webhooks/telegram/{token}
    → MessagingGateway normaliza para MessagePayload
      → Cria/atualiza Patient no CRM
        → Sessão de conversa carregada do Redis
          → AI Engine: histórico + nova mensagem → LLM
            → LLM classifica intent "agendar"
              → tool: check_availability()
                → SchedulingService → Adapter → slots livres
              → LLM monta resposta com horários disponíveis
          → Resposta enviada via Telegram
          → Conversa salva no Redis (TTL 24h) e PostgreSQL
```

## Fluxo Principal: Lead → Conversão

```
[Lead entra via Google Ads]
  → POST /api/v1/leads/webhook/inbound (X-API-Key)
    → Lead criado com status "novo"
    → SLA calculado (created_at + CLINIC_SLA_HOURS)
    → Secretária notificada via Telegram
      → Secretária acessa Kanban → abre lead → registra contato
        → status: "em_contato" → contacted_at registrado
          → Envia orçamento → status: "orcamento_enviado"
            → Paciente aceita → Convert Lead
              → Patient criado → Appointment criado
                → status: "convertido" → KPI atualizado
```

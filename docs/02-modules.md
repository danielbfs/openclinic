---
tags: [openclinic, modules]
created: 2026-04-23
status: draft
---

# Módulos — Open Clinic AI

## Estrutura de Diretórios

```
backend/app/modules/
├── auth/           Autenticação e autorização
├── messaging/      Gateway de mensagens (Telegram, WhatsApp)
├── ai/             Engine de IA (LLM + function calling)
├── scheduling/     Serviço de agendamento (abstração + adapters)
├── crm/            Pacientes e histórico
├── leads/          Gestão de leads, SLA, pipeline, relatórios
├── followup/       Follow-up automático (Celery tasks)
└── admin/          Configurações e setup wizard
```

---

## auth

**Responsabilidade:** Autenticação JWT, controle de acesso por role (RBAC).

| Arquivo | Função |
|---|---|
| `router.py` | Endpoints: `/auth/login`, `/auth/refresh`, `/auth/logout` |
| `service.py` | Geração e validação de JWT, hash de senha |
| `models.py` | `User` (id, email, full_name, role, is_active) |
| `schemas.py` | `LoginRequest`, `TokenResponse` |

**Roles:**
- `admin` — acesso total, incluindo setup e relatórios
- `secretary` — acesso ao calendário, leads e agendamentos

---

## messaging

**Responsabilidade:** Receber mensagens de canais externos, normalizar para formato interno, enviar respostas.

| Arquivo | Função |
|---|---|
| `router.py` | Webhooks: `POST /webhooks/telegram/{token}`, `POST /webhooks/whatsapp/{token}` |
| `gateway.py` | Roteamento: recebe `MessagePayload`, chama AI Engine, despacha resposta |
| `schemas.py` | `MessagePayload` — formato normalizado independente de canal |
| `adapters/base.py` | `AbstractMessagingAdapter` |
| `adapters/telegram.py` | Parsing de update Telegram, envio via Bot API |
| `adapters/evolution_api.py` | Integração com WhatsApp via Evolution API (WebSocket/Webhook) |

**Segurança:** Webhooks validados por `secret_token` (Telegram) ou HMAC (WhatsApp).

---

## ai

**Responsabilidade:** Gerenciar sessão de conversa, chamar LLM, executar tools (function calling) e orquestrar streaming para IA Visual.

| Arquivo | Função |
|---|---|
| `engine.py` | Orquestrador: monta contexto, chama LLM, executa tools, suporte a stream para avatar |
| `session.py` | Histórico de conversa no Redis (TTL 24h), fallback para DB |
| `tools.py` | Definição das tools disponíveis (agendamento, FAQ, triagem) |
| `prompts.py` | System prompt base + templates de personalidade do avatar |
| `adapters/visual_ai.py` | Orquestração de tokens e sessões para HeyGen / Hume AI |

**Novas Funcionalidades (Roadmap 2.0):**
- **Streaming Mode:** Redução de latência para conversas por voz/avatar.
- **Voice-to-Intent:** Processamento de transcrições vindas do frontend.

**Tools disponíveis para o LLM:**
- `check_availability(specialty_id, date_from, date_to)`
- `book_appointment(doctor_id, starts_at, patient_notes)`
- `cancel_appointment(appointment_id)`
- `reschedule_appointment(appointment_id, new_starts_at)`
- `get_patient_appointments()`
- `escalate_to_human(reason)`

---

## scheduling

**Responsabilidade:** Abstração do sistema de agendamento — interface unificada independente do provider (Google Calendar ou banco local).

| Arquivo | Função |
|---|---|
| `service.py` | `SchedulingService`: `get_available_slots()`, `book_appointment()`, `cancel_appointment()`, `reschedule_appointment()` |
| `router.py` | Endpoints de slots, calendário, bloqueios |
| `availability.py` | Algoritmo de cálculo de slots livres |
| `conflict.py` | Detecção de conflito + lock otimista |
| `adapters/base.py` | `AbstractSchedulingAdapter` |
| `adapters/google_calendar.py` | freebusy query, OAuth, criação de eventos |
| `adapters/local_db.py` | Leitura de `doctor_schedules` + `appointments` |

---

## crm

**Responsabilidade:** Cadastro e histórico de pacientes (já convertidos — tiveram ao menos um agendamento).

| Arquivo | Função |
|---|---|
| `router.py` | CRUD de pacientes, histórico de conversas e agendamentos |
| `service.py` | get_or_create_patient (por telefone), atualização de status |
| `models.py` | `Patient` |
| `schemas.py` | `PatientCreate`, `PatientUpdate`, `PatientResponse` |

---

## leads

**Responsabilidade:** Pipeline de leads pré-agendamento, SLA de retorno, interações da equipe, conversão, webhook de entrada externa, relatórios.

| Arquivo | Função |
|---|---|
| `router.py` | CRUD leads, pipeline actions, interações, webhook inbound, relatórios |
| `service.py` | Regras de negócio: SLA calc, conversão lead→paciente, atribuição |
| `models.py` | `Lead`, `LeadInteraction` |
| `schemas.py` | Schemas de entrada/saída |
| `sla.py` | Celery task: verifica leads vencidos a cada 15 min, notifica responsável |
| `reports.py` | Queries SQL de relatório (funil, origem, conversão, SLA, campanhas) |

**Pipeline:** `novo → em_contato → orcamento_enviado → negociando → convertido | perdido`

---

## followup

**Responsabilidade:** Envio automático de mensagens baseado em eventos de agendamento.

| Arquivo | Função |
|---|---|
| `tasks.py` | Celery tasks: `send_followup_message(job_id)` |
| `scheduler.py` | Ao criar/alterar agendamento, agenda jobs conforme regras |
| `router.py` | CRUD de regras e histórico de execuções |
| `models.py` | `FollowupRule`, `FollowupJob` |

**Triggers suportados:** `appointment_scheduled`, `appointment_confirmed`, `appointment_cancelled`, `no_show`

---

## admin

**Responsabilidade:** Setup wizard e configurações globais do sistema.

| Arquivo | Função |
|---|---|
| `router.py` | Endpoints de setup, settings, OAuth Google, audit logs |
| `setup_wizard.py` | Validação e persistência de cada etapa do wizard |
| `schemas.py` | Schemas de configuração por módulo |

**Configurações gerenciadas:**
- Informações da clínica (nome, timezone, SLA hours)
- Integração Telegram / WhatsApp
- Provider de LLM (OpenAI ou Local)
- Provider de agenda (Google Calendar ou Local)
- Regras de follow-up
- API key para webhook de leads externos

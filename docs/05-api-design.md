---
tags: [openclinic, api]
created: 2026-04-23
status: draft
---

# Design da API — Open Clinic AI

## Convenções

- Base URL: `/api/v1/`
- Autenticação: `Authorization: Bearer {access_token}` (JWT)
- Formato: JSON
- Paginação: `?page=1&page_size=20`

### Padrão de Resposta

```json
// Sucesso (lista)
{
  "data": [...],
  "meta": {"page": 1, "page_size": 20, "total": 150}
}

// Sucesso (item)
{
  "data": {...}
}

// Erro
{
  "error": {
    "code": "SLOT_NOT_AVAILABLE",
    "message": "O horário selecionado não está mais disponível.",
    "detail": {}
  }
}
```

---

## Auth

```
POST /auth/login
  Body: {email, password}
  Returns: {access_token, refresh_token, user: {id, name, role}}

POST /auth/refresh
  Body: {refresh_token}
  Returns: {access_token}

POST /auth/logout
  Body: {refresh_token}
  Returns: 204 No Content
```

---

## Webhooks (sem auth — validados por token/signature)

```
POST /webhooks/telegram/{bot_token}
  Header: X-Telegram-Bot-Api-Secret-Token: {secret}
  Body: Telegram Update object

POST /webhooks/whatsapp/{token}
  Header: X-Hub-Signature-256: sha256={hmac}
  Body: Evolution API webhook payload
```

---

## Patients / CRM

```
GET    /patients
  Params: status, phone, name, page, page_size
  Auth: admin | secretary

GET    /patients/{id}
GET    /patients/{id}/conversations
GET    /patients/{id}/appointments

PATCH  /patients/{id}
  Body: {crm_status?, notes?}
```

---

## Leads

```
GET    /leads
  Params: status, channel, assigned_to, is_overdue,
          specialty_id, created_from, created_to,
          utm_campaign, utm_source, page, page_size

POST   /leads
  Body: {full_name, phone, email?, channel, specialty_id?,
         description?, utm_source?, utm_medium?, utm_campaign?,
         utm_content?, utm_term?, assigned_to?}

GET    /leads/{id}
PATCH  /leads/{id}
  Body: {status?, assigned_to?, next_followup_at?,
         quote_value?, description?, lost_reason?}

DELETE /leads/{id}    (admin only — soft delete)

# Pipeline actions
POST   /leads/{id}/contact
  Body: {note?}                    → seta contacted_at, status → em_contato

POST   /leads/{id}/convert
  Body: {doctor_id, starts_at, notes?}   → cria patient + appointment

PATCH  /leads/{id}/assign
  Body: {user_id}

POST   /leads/{id}/lost
  Body: {reason}                   (obrigatório)

# Interações
GET    /leads/{id}/interactions
POST   /leads/{id}/interactions
  Body: {type, content, next_action?}

# Entrada externa (Google Ads, Meta Ads, formulário)
POST   /leads/webhook/inbound
  Header: X-API-Key: {LEADS_WEBHOOK_API_KEY}
  Body: {name, phone, email?, utm_source?, utm_medium?,
         utm_campaign?, utm_content?, utm_term?, specialty?, message?}
  Returns: {lead_id, status: "created"}
```

---

## Relatórios de Leads

```
GET /reports/leads/funnel
  Params: date_from, date_to
  Returns: [{status, total}]

GET /reports/leads/by-source
  Params: date_from, date_to
  Returns: [{channel, utm_campaign, total_leads, converted, conversion_rate}]

GET /reports/leads/conversion
  Params: period (7d|30d|90d|custom), date_from?, date_to?
  Returns: {total, converted, rate, by_channel: [...]}

GET /reports/leads/sla
  Params: date_from, date_to
  Returns: {total, within_sla, overdue, sla_rate}

GET /reports/leads/time-to-contact
  Params: date_from, date_to
  Returns: [{channel, avg_hours, contacted, overdue_total}]

GET /reports/leads/campaigns
  Params: date_from, date_to
  Returns: [{utm_campaign, utm_source, leads, converted, rate}]

GET /reports/leads/by-user
  Params: date_from, date_to
  Returns: [{assignee, total_leads, converted, avg_contact_hours}]

GET /reports/leads/timeline
  Params: date_from, date_to
  Returns: [{day, new_leads, converted}]

GET /reports/appointments/overview
  Params: date_from, date_to, doctor_id?
  Returns: {total, by_status: {...}, by_doctor: [...]}

GET /reports/revenue/estimates
  Params: date_from, date_to
  Returns: [{channel, converted_value, pipeline_value}]
```

**Export CSV:** todos os endpoints de relatório aceitam `?format=csv` → retorna `Content-Type: text/csv`.

---

## Agendamentos

```
GET    /appointments
  Params: doctor_id, date_from, date_to, status, patient_id

POST   /appointments
  Body: {patient_id, doctor_id, specialty_id, starts_at, ends_at, notes?, source?}

GET    /appointments/{id}
PATCH  /appointments/{id}
  Body: {status?, notes?}

DELETE /appointments/{id}    → cancela (status = cancelled)
```

---

## Scheduling

```
GET  /scheduling/slots
  Params: doctor_id | specialty_id, date_from, date_to
  Returns: [{starts_at, ends_at, doctor_id, doctor_name, is_available}]

GET  /scheduling/calendar
  Params: date_from, date_to
  Returns: visão consolidada todos os médicos

POST /scheduling/blocks
  Body: {doctor_id, starts_at, ends_at, reason?}

DELETE /scheduling/blocks/{id}
```

---

## Doctors

```
GET    /doctors
POST   /doctors
  Body: {full_name, crm?, specialty_id, scheduling_provider,
         provider_config?, slot_duration_minutes?}
GET    /doctors/{id}
PATCH  /doctors/{id}
DELETE /doctors/{id}    (soft delete — is_active = false)
GET    /doctors/{id}/schedule    → regras de disponibilidade
PUT    /doctors/{id}/schedule    → substituir regras
  Body: [{day_of_week, start_time, end_time}]
```

---

## Specialties

```
GET    /specialties
POST   /specialties
PATCH  /specialties/{id}
DELETE /specialties/{id}
```

---

## Follow-up Rules

```
GET    /followup/rules
POST   /followup/rules
PATCH  /followup/rules/{id}
DELETE /followup/rules/{id}
GET    /followup/jobs
  Params: status, date_from, date_to
```

---

## Admin / Setup

```
GET  /admin/setup/status
  Returns: {messaging: bool, ai: bool, scheduling: bool, clinic_info: bool}

POST /admin/setup/messaging
  Body: {provider: "telegram"|"whatsapp", config: {...}}

POST /admin/setup/ai
  Body: {provider: "openai"|"local_llm", config: {model, api_key_ref?, base_url?}}

POST /admin/setup/scheduling
  Body: {default_provider: "local_db"|"google_calendar"}

GET  /admin/settings
PATCH /admin/settings/clinic
  Body: {name, timezone, sla_hours, leads_webhook_api_key?}

POST /admin/google/oauth      → inicia fluxo OAuth
GET  /admin/google/callback   → callback OAuth (redirect)

GET  /admin/audit-logs
  Params: user_id, action, entity_type, date_from, date_to
```

---
tags: [openclinic, roadmap]
created: 2026-04-23
status: draft
---

# Roadmap — Open Clinic AI

## Phase 1 — MVP (8–10 semanas)

**Objetivo:** Clínica consegue receber pacientes pelo Telegram, agendar, gerenciar leads com SLA e visualizar na interface da secretária.

### Infra e Base
- [ ] Scaffold completo (Docker, FastAPI, Next.js, PostgreSQL, Redis, Traefik)
- [ ] Migrations com Alembic
- [ ] Auth (JWT, roles admin/secretary)
- [ ] CI/CD básico (GitHub Actions → build)

### Backend
- [ ] CRM — CRUD de pacientes
- [ ] Módulo de especialidades e médicos
- [ ] SchedulingService — adapter `local_db`
- [ ] Regras de disponibilidade (doctor_schedules)
- [ ] Cálculo de slots disponíveis
- [ ] Agendamentos (criação, cancelamento, constraint de conflito)
- [ ] **Leads — CRUD + pipeline + interações**
- [ ] **SLA de leads — Celery Beat, check 15min, notificação**
- [ ] **Webhook de entrada de leads externos (/leads/webhook/inbound)**
- [ ] **Conversão lead → paciente → agendamento**
- [ ] Integração Telegram (webhook + envio)
- [ ] AI Engine com OpenAI (tools: check_availability, book_appointment, cancel, reschedule)
- [ ] Follow-up: lembrete 24h antes (Celery)
- [ ] Audit log

### Frontend
- [ ] Auth (login, proteção de rotas por role)
- [ ] Interface Secretária: calendário de agendamentos
- [ ] Interface Secretária: agendamento manual
- [ ] **Interface Secretária: Kanban de leads**
- [ ] **Interface Secretária: detalhe do lead + interações**
- [ ] Admin Wizard: setup clínica, Telegram, OpenAI, SLA
- [ ] Admin: gestão de médicos, especialidades, disponibilidade

### Relatórios (MVP)
- [ ] **Funil de leads (por status)**
- [ ] **Leads por origem/canal**
- [ ] **SLA compliance**

---

## Phase 2 (10 semanas após MVP aprovado)

### Mensageria
- [ ] WhatsApp via Evolution API

### Agendamento
- [ ] Google Calendar adapter + fluxo OAuth

### IA
- [ ] Local LLM support (Ollama / LM Studio)
- [ ] Prompt configurável pelo admin

### Leads e Marketing
- [ ] **Integração nativa Meta Lead Ads (webhook oficial)**
- [ ] **Integração Google Ads Lead Form Extension**
- [ ] **Relatórios avançados: campanhas UTM, receita estimada**
- [ ] **Performance por secretária**
- [ ] **Export CSV em todos os relatórios**

### Follow-up
- [ ] No-show recovery automático
- [ ] Follow-up pós-consulta (avaliação)
- [ ] Configuração completa via admin panel

### Qualidade
- [ ] Testes automatizados (pytest, cobertura ≥70%)
- [ ] GitHub Actions: build + push imagens GHCR
- [ ] Documentação de contribuição (CONTRIBUTING.md)

---

## Phase 3 — Roadmap Futuro

- [ ] Dashboard executivo consolidado (todos os KPIs em uma tela)
- [ ] Multi-idioma (i18n) — inglês, espanhol
- [ ] Prontuário eletrônico básico (PEP) — anamnese, prescrições
- [ ] API pública para integrações de terceiros
- [ ] App mobile para secretária (React Native)
- [ ] Sistema de avaliações pós-consulta (NPS automatizado)
- [ ] Integração com CRMs externos (RD Station, HubSpot) via webhook out
- [ ] Script de instalação automatizado one-liner com prompt interativo

---

## Ordem de Implementação dos Módulos

```
1.  Auth
2.  CRM (patients)
3.  Doctors + Specialties
4.  SchedulingService (local_db adapter)
5.  Appointments
6.  Leads + SLA + Interações
7.  Relatórios de Leads (básico)
8.  Messaging (Telegram webhook)
9.  AI Engine (OpenAI + tools)
10. Follow-up (Celery)
11. Admin Wizard
12. Integrações externas (Google Calendar, WhatsApp, Meta Ads)
```

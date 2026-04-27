---
tags: [openclinic, roadmap]
created: 2026-04-27
status: active
version: 2.0
---

# Roadmap 2.0 — Open Clinic AI

Este roadmap prioriza a experiência do paciente e o retorno sobre investimento (ROI) da clínica, focando em humanização via IA Visual e dominância do canal WhatsApp.

## Phase 1 — MVP & Consolidação (Conclusão)

**Objetivo:** Fluxo base funcional para operação interna da clínica e recepção via Telegram.

### Infra e Base
- [x] Scaffold completo (Docker, FastAPI, Next.js, PostgreSQL, Redis, Traefik)
- [x] Migrations com Alembic
- [x] Auth (JWT, roles admin/secretary)
- [x] CI/CD básico (GitHub Actions)

### Backend & Core
- [x] CRM — CRUD de pacientes e histórico
- [x] Módulo de especialidades e médicos
- [x] SchedulingService — adapter `local_db`
- [x] Regras de disponibilidade e cálculo de slots
- [x] Agendamentos (criação, cancelamento, conflitos)
- [x] Leads — CRUD, pipeline e interações
- [x] SLA de leads — Celery Beat + Notificações Telegram
- [x] Webhook de entrada de leads externos
- [x] AI Engine — Function calling (check, book, cancel)
- [x] Follow-up — Lembretes básicos via Celery
- [ ] **Ajuste:** Audit Log detalhado para conformidade médica (em progresso)
- [ ] **Ajuste:** Dashboard de Conversão Real (leads vs. agendamentos efetivados)

### Frontend
- [x] Interface Secretária: Calendário e Agendamento Manual
- [x] Interface Secretária: Kanban de Leads e Detalhes
- [x] Admin: Gestão de médicos, especialidades e horários
- [x] Admin Wizard: Setup inicial da clínica e integrações

---

## Phase 2 — A "Secretária do Futuro" (Próximos Passos)

**Objetivo:** Transformar o atendimento digital em uma experiência humana e proativa que gera vendas.

### Experiência Visual e Voz (IA Visual)
- [ ] **Integração HeyGen/Hume AI:** Streaming de Avatar em tempo real no site da clínica.
- [ ] **Voice-to-Intent:** Interface de voz para agendamento natural sem digitação.
- [ ] **Setup do Avatar:** Escolha de rosto e personalidade da "Secretária Virtual" no Admin.

### Mensageria Dominante
- [ ] **WhatsApp (Evolution API):** Integração completa como canal principal.
- [ ] **Shared Inbox:** Interface para secretária humana assumir conversas do WhatsApp.
- [ ] **Notificações Ativas:** Confirmação de consulta via áudio ou texto natural no WhatsApp.

### Inteligência de Ocupação (ROI)
- [ ] **Recuperação de No-show:** Oferta ativa de vagas remanescentes para leads em espera.
- [ ] **Antecipação de Agenda:** IA detecta buracos na agenda e convida pacientes de datas distantes para antecipar.
- [ ] **SLA 2.0:** Alerta visual crítico no dashboard para leads sem contato humano > 30min.

---

## Phase 3 — Marketing, Finanças e Ecossistema

**Objetivo:** Escalar a operação e integrar com o fluxo financeiro e médico.

### Finanças e Vendas
- [ ] **Pagamento Antecipado:** Integração com Stripe/Asaas para procedimentos.
- [ ] **Relatórios de ROI:** Custo por agendamento e performance de campanhas (UTMs).
- [ ] **Comissionamento:** Relatório de conversão por secretária.

### Integrações Médicas
- [ ] **Google Calendar Adapter:** Sincronia bidirecional para médicos externos.
- [ ] **Integração EMR/PEP:** Fluxo de dados para prontuários eletrônicos (FHIR).
- [ ] **NPS Automatizado:** Coleta de satisfação pós-atendimento.

### Globalização e Escala
- [ ] **Suporte a Local LLM:** (Opcional) para clínicas com alta demanda de privacidade.
- [ ] **Multi-idioma (i18n):** Inglês e Espanhol.
- [ ] **App Mobile (PWA):** Para notificações push em tempo real na mão da secretária.

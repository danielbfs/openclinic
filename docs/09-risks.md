---
tags: [openclinic, risks]
created: 2026-04-23
status: draft
---

# Riscos e Mitigações — Open Clinic AI

## Tabela de Riscos

| # | Risco | Prob. | Impacto | Mitigação |
|---|---|---|---|---|
| 1 | Race condition em agendamentos simultâneos | Média | Alto | EXCLUDE constraint + SELECT FOR UPDATE + Redis lock de 5min no slot |
| 2 | Token Google Calendar expirado em produção | Alta | Alto | Refresh automático + alerta admin + health check periódico |
| 3 | LLM alucinar horários disponíveis | Média | Alto | Tool obrigatória — LLM nunca inventa horário sem chamar check_availability |
| 4 | Webhook Telegram cair (bot offline) | Baixa | Alto | Health check + alerta admin + re-registro automático do webhook |
| 5 | LGPD — dados de saúde dos pacientes | Alta | Crítico | Encryption at rest (PG), audit log de acesso, política de retenção, backup seguro |
| 6 | Custo OpenAI elevado com alto volume | Média | Médio | Cache de respostas, modelo menor default (gpt-4o-mini), suporte a Local LLM |
| 7 | Conflito ao migrar de local_db para Google Calendar | Baixa | Alto | Wizard de migração com verificação de conflitos antes da troca |
| 8 | VPS sem recursos para Ollama/Local LLM | Alta | Médio | Requisitos documentados; default é OpenAI API |
| 9 | Lead não atribuído fica sem retorno (SLA vence) | Média | Alto | Atribuição automática round-robin + alerta por Telegram ao admin |
| 10 | Webhook de leads externos aberto na internet | Alta | Médio | API key obrigatória + rate limiting via Traefik + validação de payload |

---

## Detalhamento

### 1. Race Condition em Agendamentos

**Cenário real:** Dois pacientes diferentes escolhem o mesmo horário do mesmo médico ao mesmo tempo. Sem proteção, ambos confirmam e o médico recebe dois agendamentos sobrepostos.

**Mitigação em camadas:**
1. **Redis lock** (5 min) ao exibir slot — slot não é ofertado para outro paciente enquanto o primeiro está confirmando
2. **SELECT FOR UPDATE** na transação de criação — bloqueia a linha no banco durante a inserção
3. **EXCLUDE constraint** PostgreSQL — última barreira, rejeita no banco se tudo mais falhar

---

### 2. Token Google Calendar Expirado

**Cenário real:** O médico configurou o Google Calendar, mas o refresh token expirou (inativo >6 meses ou permissão revogada). Sistema começa a falhar silenciosamente nos agendamentos via Google.

**Mitigação:**
- Celery Beat: health check diário por médico com GCal configurado
- Se falhar: alerta para admin via Telegram + marca provider como "offline" no painel
- Admin pode revogar e reconfigar OAuth sem downtime

---

### 3. LLM Alucinação de Horários

**Cenário real:** O LLM responde "você pode agendar amanhã às 14h" sem verificar disponibilidade, e o paciente confirma — mas o slot está ocupado.

**Mitigação:**
- System prompt com regra explícita: "NUNCA confirme horários sem usar check_availability"
- Validação na tool `book_appointment`: sempre verifica disponibilidade antes de criar
- Se conflito: LLM recebe erro e oferece alternativas

---

### 5. LGPD — Dados de Saúde

**Dados sensíveis armazenados:**
- Nome, telefone, e-mail dos pacientes
- Histórico de mensagens (pode conter queixas clínicas)
- Notas de consultas

**Medidas:**
- Encryption at rest no PostgreSQL (via pgcrypto ou disk-level na VPS)
- Audit log de todo acesso a dados de pacientes
- Política de retenção de dados (configurável pelo admin — ex: apagar dados após X anos)
- Backup criptografado
- Documentação de DPA (Data Processing Agreement) para clínicas

---

### 9. SLA de Leads Vencendo sem Responsável

**Cenário real:** Lead entra às 22h. Secretária responsável só vê na manhã seguinte. SLA de 2h venceu.

**Mitigação:**
- Atribuição automática ao abrir horário (round-robin entre secretárias ativas)
- SLA configurável por horário (ex: leads fora do horário comercial têm SLA contado a partir das 8h)
- Notificação ao admin se lead ficar sem contato por X horas além do SLA
- Relatório diário automático de leads vencidos

---

### 10. Webhook de Leads Externos

**Cenário real:** Endpoint público `/leads/webhook/inbound` recebe spam ou ataque DDoS.

**Mitigações:**
- Header `X-API-Key` obrigatório (chave gerada por clínica, rotacionável)
- Rate limiting via Traefik: máx 100 req/min por IP
- Validação estrita do payload (Pydantic rejeita campos extras)
- Log de todas as tentativas (válidas e inválidas) no audit_log

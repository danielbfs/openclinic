---
tags: [openclinic, overview]
created: 2026-04-23
status: draft
---

# Open Clinic AI — Visão Geral

## O que é

Open Clinic AI é um sistema open-source para clínicas automatizarem toda a jornada do paciente — desde o primeiro contato até o pós-atendimento — usando Inteligência Artificial.

**Modelo de deploy:** uma VPS por clínica (isolamento total de dados). Cada clínica instala sua própria instância a partir do repositório público no GitHub.

## Problema que resolve

Clínicas pequenas e médias perdem leads e pacientes por:
- Demora no retorno a interessados (WhatsApp, Instagram, Google)
- Agendamento manual e sujeito a erros de sobreposição
- Falta de follow-up automatizado (lembretes, confirmações, reengajamento)
- Nenhuma rastreabilidade de origem dos leads (Google Ads, Meta Ads)
- Dados de conversão invisíveis para a gestão

## Funcionalidades Principais

| Módulo | Descrição |
|---|---|
| **Chatbot IA** | Atendimento via Telegram e WhatsApp — agenda, cancela, remarca |
| **Agendamento** | Multi-médico, multi-especialidade, com bloqueio de conflitos |
| **Gestão de Leads** | Pipeline de conversão, SLA de retorno, integração com tráfego pago |
| **Follow-up** | Lembretes automáticos 24h/2h antes, recuperação de no-show |
| **Interface Secretária** | Calendário, kanban de leads, agendamento manual |
| **Painel Admin** | Setup wizard, configurações, relatórios completos |
| **Relatórios** | Funil, origem, SLA, performance de campanhas, receita estimada |

## Público-alvo

- Clínicas médicas, odontológicas e de estética
- 1 a 20 profissionais de saúde por unidade
- Equipe administrativa com secretárias/recepcionistas

## Repositório

https://github.com/danielbfs/openclinic

## Links desta documentação

- [[01-architecture]] — Arquitetura técnica
- [[02-modules]] — Módulos e responsabilidades
- [[03-database-schema]] — Schema do banco de dados
- [[04-scheduling-system]] — Sistema de agendamento
- [[05-api-design]] — Design da API
- [[06-ai-design]] — Engine de IA
- [[07-deployment]] — Deploy e infraestrutura
- [[08-roadmap]] — Roadmap de desenvolvimento
- [[09-risks]] — Riscos e mitigações

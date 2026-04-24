# Open Clinic AI

Sistema open-source para clínicas automatizarem comunicação com pacientes via IA, agendamento multi-médico, gestão de leads e follow-up automático.

> **Uma VPS por clínica. Deploy em 5 minutos.**

---

## Funcionalidades

- **Chatbot IA** via Telegram e WhatsApp — agendamento, cancelamento e remarcação automatizados
- **Agendamento multi-médico** com controle de disponibilidade e prevenção de conflitos
- **Gestão de Leads** com pipeline de conversão, SLA de retorno e integração com Google Ads / Meta Ads
- **Follow-up automático** — lembretes, confirmações e recuperação de no-show
- **Interface da Secretária** — calendário, kanban de leads e agendamento manual
- **Painel Administrativo** — setup wizard, configurações e relatórios
- **Relatórios** — funil de conversão, origem dos leads, SLA compliance, performance por campanha

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | FastAPI (Python 3.12) + Celery |
| Frontend | Next.js 14 + TypeScript + Shadcn/ui |
| Banco de dados | PostgreSQL 16 |
| Cache / Fila | Redis 7 |
| Proxy / SSL | Traefik v3 + Let's Encrypt |
| Deploy | Docker + Docker Compose |

---

## Deploy Rápido (VPS Hostinger)

### Pré-requisitos

- VPS Ubuntu 22.04 LTS (mínimo 2 vCPU / 4GB RAM)
- Domínio apontando para o IP da VPS (registro DNS tipo A)
- Docker instalado: `curl -fsSL https://get.docker.com | sh`

### Passos

```bash
# 1. Clonar o repositório
git clone https://github.com/danielbfs/openclinic.git
cd openclinic

# 2. Configurar variáveis de ambiente
cp .env.example .env
nano .env   # preencher DOMAIN, senhas e tokens

# 3. Ajustar permissão do arquivo de certificados SSL
touch traefik/acme.json && chmod 600 traefik/acme.json

# 4. Subir os serviços
docker compose up -d

# 5. Migrations + criar admin inicial
./install.sh
```

Acesse `https://seu-dominio.com` — SSL provisionado automaticamente pelo Traefik.

### Credenciais Iniciais

Após rodar `./install.sh`, os seguintes usuários são criados:

| Usuário | Senha | Role |
|---|---|---|
| `admin` | `admin` | admin |
| `secretaria` | `secretaria` | secretary |

> **IMPORTANTE:** Altere as senhas no primeiro acesso via menu "Alterar Senha".

### Atualizar para nova versão

```bash
./update.sh
```

---

## Desenvolvimento Local

```bash
# Clonar e entrar no diretório
git clone https://github.com/danielbfs/openclinic.git
cd openclinic

# Configurar ambiente
cp .env.example .env
# Editar .env com configurações locais (sem DOMAIN/ACME_EMAIL)

# Subir em modo dev (sem Traefik, com hot reload e portas expostas)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

---

## Variáveis de Ambiente

Veja `.env.example` com todas as variáveis documentadas e comentadas.

Variáveis obrigatórias para produção:

| Variável | Descrição |
|---|---|
| `DOMAIN` | Domínio da clínica (ex: `clinica.seudominio.com`) |
| `ACME_EMAIL` | E-mail para o Let's Encrypt |
| `DB_PASSWORD` | Senha do PostgreSQL |
| `SECRET_KEY` | Chave secreta JWT (mín. 64 chars) |
| `TELEGRAM_BOT_TOKEN` | Token do bot Telegram |
| `OPENAI_API_KEY` | Chave da API OpenAI |

---

## Documentação

A documentação completa está em [`docs/`](docs/) — formatada para Obsidian.

| Arquivo | Conteúdo |
|---|---|
| [00-overview.md](docs/00-overview.md) | Visão geral e objetivos |
| [01-architecture.md](docs/01-architecture.md) | Arquitetura e decisões técnicas |
| [02-modules.md](docs/02-modules.md) | Módulos e responsabilidades |
| [03-database-schema.md](docs/03-database-schema.md) | Schema do banco de dados |
| [04-scheduling-system.md](docs/04-scheduling-system.md) | Sistema de agendamento |
| [05-api-design.md](docs/05-api-design.md) | Design da API |
| [06-ai-design.md](docs/06-ai-design.md) | Engine de IA e function calling |
| [07-deployment.md](docs/07-deployment.md) | Deploy, Docker e Traefik |
| [08-roadmap.md](docs/08-roadmap.md) | Roadmap de desenvolvimento |
| [09-risks.md](docs/09-risks.md) | Riscos e mitigações |

---

## Contribuindo

Contribuições são bem-vindas! Por favor leia [CONTRIBUTING.md](CONTRIBUTING.md) antes de abrir um PR.

1. Fork o repositório
2. Crie uma branch: `git checkout -b feature/minha-feature`
3. Commit: `git commit -m 'feat: adiciona minha feature'`
4. Push: `git push origin feature/minha-feature`
5. Abra um Pull Request

---

## Licença

MIT License — veja [LICENSE](LICENSE) para detalhes.

---

> Desenvolvido para a comunidade de clínicas. Cada instância é independente — seus dados ficam na sua VPS.

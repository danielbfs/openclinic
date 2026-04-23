---
tags: [openclinic, deployment, docker, traefik]
created: 2026-04-23
status: draft
---

# Deploy — Open Clinic AI

## Estratégia

- **Arquivo principal:** `docker-compose.yml` na raiz do repo = **produção** com Traefik
- **Override local:** `docker-compose.override.yml` = dev (aplicado automaticamente)
- **SSL:** Traefik + Let's Encrypt (HTTP-01 challenge automático)
- **Deploy a partir do GitHub:** `git clone URL → cp .env.example .env → docker compose up -d`

---

## Serviços Docker

| Serviço | Imagem | Função |
|---|---|---|
| `traefik` | traefik:v3.1 | Reverse proxy + SSL automático |
| `db` | postgres:16-alpine | Banco de dados principal |
| `redis` | redis:7-alpine | Cache de sessão + fila Celery |
| `backend` | build ./backend | FastAPI API |
| `frontend` | build ./frontend | Next.js UI |
| `celery_worker` | build ./backend | Workers assíncronos |
| `celery_beat` | build ./backend | Cron scheduler |

## Redes Docker

| Rede | Serviços | Descrição |
|---|---|---|
| `openclinic_proxy` | traefik, backend, frontend | Tráfego HTTP/HTTPS |
| `openclinic_internal` | db, redis, workers, backend, frontend | Comunicação interna |

DB e Redis **não têm portas expostas** em produção.

---

## Passo a Passo: Deploy na Hostinger VPS

### 1. Criar VPS
- Ubuntu 22.04 LTS
- Mínimo: 2 vCPU / 4GB RAM / 40GB SSD
- (Com Ollama/Local LLM: 8+ vCPU / 16GB RAM / 80GB SSD)

### 2. Configurar DNS
- Registro A: `seudominio.com` → IP da VPS
- Registro A: `traefik.seudominio.com` → mesmo IP (opcional, para dashboard)
- Aguardar propagação (pode levar até 24h, geralmente <5min)

### 3. Instalar Docker na VPS
```bash
curl -fsSL https://get.docker.com | sh
usermod -aG docker $USER
newgrp docker
```

### 4. Liberar Firewall (Hostinger Firewall Rules)
```
80/tcp  → Allow (Let's Encrypt challenge)
443/tcp → Allow (HTTPS)
22/tcp  → Allow (SSH — restrinja ao seu IP se possível)
```

### 5. Clonar e Configurar
```bash
git clone https://github.com/danielbfs/openclinic.git
cd openclinic

cp .env.example .env
nano .env
# Preencher: DOMAIN, ACME_EMAIL, DB_PASSWORD, SECRET_KEY,
#            TELEGRAM_BOT_TOKEN, OPENAI_API_KEY
```

### 6. Preparar arquivo SSL
```bash
touch traefik/acme.json
chmod 600 traefik/acme.json  # OBRIGATÓRIO — Traefik recusa se permissão errada
```

### 7. Subir serviços
```bash
docker compose up -d
```

### 8. Instalar (migrations + admin)
```bash
./install.sh
```

### 9. Verificar SSL
```bash
# Aguardar ~30 segundos após o compose up
curl -I https://seudominio.com
# Deve retornar HTTP/2 200
```

---

## Arquivos de Configuração Traefik

### traefik/traefik.yml
```yaml
entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
          permanent: true
  websecure:
    address: ":443"

certificatesResolvers:
  letsencrypt:
    acme:
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web

providers:
  docker:
    exposedByDefault: false
    network: openclinic_proxy
  file:
    directory: /etc/traefik/dynamic
    watch: true
```

### traefik/dynamic/middlewares.yml
Contém: `security-headers`, `webhook-ratelimit`, `api-ratelimit`.

---

## Roteamento

| URL | Destino |
|---|---|
| `http://seudominio.com/*` | Redireciona para HTTPS |
| `https://seudominio.com/api/*` | backend:8000 |
| `https://seudominio.com/webhooks/*` | backend:8000 |
| `https://seudominio.com/*` | frontend:3000 |
| `https://traefik.seudominio.com` | Traefik dashboard (auth) |

---

## Atualização

```bash
./update.sh
# Faz: git pull → docker compose build → up -d → alembic upgrade head
```

---

## Desenvolvimento Local

```bash
# Override é aplicado automaticamente (sem Traefik, portas expostas)
docker compose up -d

# Backend com hot reload: http://localhost:8000
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
# DB: localhost:5432 (DBeaver, pgAdmin)
# Redis: localhost:6379
```

---

## Monitoramento

```bash
# Logs em tempo real
docker compose logs -f backend
docker compose logs -f celery_worker

# Status dos serviços
docker compose ps

# Uso de recursos
docker stats
```

---

## Backup do Banco

```bash
# Dump manual
docker compose exec db pg_dump -U openclinic openclinic > backup_$(date +%Y%m%d).sql

# Restore
docker compose exec -T db psql -U openclinic openclinic < backup.sql
```

Recomendação: configurar backup automático diário no cron da VPS para um bucket S3 ou similar.

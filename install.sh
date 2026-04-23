#!/usr/bin/env bash
# ============================================================
# Open Clinic AI — Script de Instalação
# Executar APÓS: docker compose up -d
# ============================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║         Open Clinic AI — Instalação      ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Verificar pré-requisitos
command -v docker >/dev/null 2>&1 || error "Docker não encontrado. Instale: curl -fsSL https://get.docker.com | sh"
docker compose version >/dev/null 2>&1 || error "Docker Compose v2 não encontrado."

# Verificar .env
[ -f ".env" ] || error "Arquivo .env não encontrado. Execute: cp .env.example .env && nano .env"

# Verificar variáveis obrigatórias
source .env
[ -z "$DB_PASSWORD" ]  && error "DB_PASSWORD não configurado no .env"
[ -z "$SECRET_KEY" ]   && error "SECRET_KEY não configurado no .env"

# Arquivo de certificados SSL (Traefik exige permissão 600)
if [ ! -f "traefik/acme.json" ]; then
    info "Criando traefik/acme.json..."
    touch traefik/acme.json
    chmod 600 traefik/acme.json
fi

# Aguardar banco de dados
info "Aguardando banco de dados ficar pronto..."
RETRIES=30
until docker compose exec -T db pg_isready -U openclinic -q 2>/dev/null; do
    RETRIES=$((RETRIES-1))
    [ $RETRIES -eq 0 ] && error "Banco de dados não respondeu após 30 tentativas."
    sleep 2
done
info "Banco de dados pronto."

# Migrations
info "Rodando migrations do banco de dados..."
docker compose exec -T backend alembic upgrade head

# Criar usuário administrador
info "Criando usuário administrador inicial..."
docker compose exec -T backend python -m app.scripts.create_admin

# Registrar webhook do Telegram (se token configurado)
if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$DOMAIN" ]; then
    info "Registrando webhook do Telegram..."
    WEBHOOK_URL="https://${DOMAIN}/webhooks/telegram/${TELEGRAM_BOT_TOKEN}"
    RESPONSE=$(curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook?url=${WEBHOOK_URL}&secret_token=${SECRET_KEY:0:32}")
    echo "$RESPONSE" | grep -q '"ok":true' && info "Webhook Telegram registrado com sucesso." || warning "Falha ao registrar webhook Telegram. Verifique manualmente."
fi

DOMAIN_VALUE=$(grep ^DOMAIN .env | cut -d= -f2 | tr -d '"')
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║        Instalação concluída!             ║"
echo "╚══════════════════════════════════════════╝"
echo ""
info "Acesse: https://${DOMAIN_VALUE}"
info "SSL será provisionado automaticamente pelo Traefik."
info "Admin: https://${DOMAIN_VALUE}/admin"
echo ""
warning "Guarde as credenciais do administrador exibidas acima!"

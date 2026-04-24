#!/usr/bin/env bash
# ============================================================
# Open Clinic AI — Script de Pós-Deploy
# Executar APÓS: docker compose up -d
# Roda migrations e cria o admin inicial.
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
echo "║     Open Clinic AI — Pós-Deploy          ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Verificar pré-requisitos
command -v docker >/dev/null 2>&1 || error "Docker não encontrado."
docker compose version >/dev/null 2>&1 || error "Docker Compose v2 não encontrado."

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

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║        Instalação concluída!             ║"
echo "╚══════════════════════════════════════════╝"
echo ""
info "O Traefik externo da Hostinger cuida do SSL."
info "Verifique se o domínio está acessível via HTTPS."
echo ""
warning "Guarde as credenciais do administrador exibidas acima!"

#!/usr/bin/env bash
# Publica a branch configurada na EC2 de produção: conecta via SSH, atualiza
# o código (clone na primeira vez, git pull nas seguintes) e reconstrói/
# reinicia os containers do docker-compose.prod.yml.
#
# Uso:
#   cp infra/deploy.env.example infra/deploy.env   # uma vez, preencha os valores
#   ./infra/deploy.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/deploy.env"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "Erro: $CONFIG_FILE não encontrado." >&2
  echo "Copie infra/deploy.env.example para infra/deploy.env e preencha os valores." >&2
  exit 1
fi

# shellcheck disable=SC1090
source "$CONFIG_FILE"

: "${EC2_HOST:?defina EC2_HOST em infra/deploy.env}"
: "${SSH_KEY:?defina SSH_KEY em infra/deploy.env}"
EC2_USER="${EC2_USER:-ubuntu}"
REMOTE_DIR="${REMOTE_DIR:-Analytic-Eyes}"
BRANCH="${BRANCH:-main}"
REPO_URL="${REPO_URL:-}"

echo "==> Publicando branch '$BRANCH' em $EC2_USER@$EC2_HOST:$REMOTE_DIR"

ssh -i "$SSH_KEY" -o ConnectTimeout=10 "$EC2_USER@$EC2_HOST" bash -s <<EOF
set -euo pipefail

if [ ! -d "$REMOTE_DIR/.git" ]; then
  if [ -z "$REPO_URL" ]; then
    echo "Erro: $REMOTE_DIR não existe na EC2 e REPO_URL não foi definido em deploy.env" >&2
    exit 1
  fi
  echo "==> $REMOTE_DIR não existe ainda, clonando..."
  git clone "$REPO_URL" "$REMOTE_DIR"
fi

cd "$REMOTE_DIR"
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"

cd etl-manager
docker compose -f docker-compose.prod.yml up -d --build

echo "==> Containers depois do deploy:"
docker compose -f docker-compose.prod.yml ps
EOF

echo "==> Deploy concluído."

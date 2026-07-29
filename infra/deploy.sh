#!/usr/bin/env bash
# Publica a branch configurada na EC2 de produção via AWS SSM Run Command:
# atualiza o código (clone na primeira vez, git pull nas seguintes) e
# reconstrói/reinicia os containers do docker-compose.prod.yml.
#
# A instância não tem IP público (fica atrás do ALB, ver infra/README.md) -
# por isso o deploy não usa mais SSH, e sim o SSM (mesmo mecanismo do acesso
# administrativo via `aws ssm start-session`). Precisa da AWS CLI
# configurada localmente com permissão ssm:SendCommand /
# ssm:GetCommandInvocation para a instância, e do agente SSM na EC2 (já vem
# de fábrica nas AMIs Ubuntu usadas aqui).
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

: "${INSTANCE_ID:?defina INSTANCE_ID em infra/deploy.env (output ec2_instance_id do Terraform)}"
AWS_REGION="${AWS_REGION:-us-east-1}"
REMOTE_DIR="${REMOTE_DIR:-Analytic-Eyes}"
BRANCH="${BRANCH:-main}"
REPO_URL="${REPO_URL:-}"

AWS_ARGS=(--region "$AWS_REGION")
if [ -n "${AWS_PROFILE:-}" ]; then
  AWS_ARGS+=(--profile "$AWS_PROFILE")
fi

REMOTE_SCRIPT=$(cat <<EOF
set -euo pipefail
cd /home/ubuntu

if [ ! -d "$REMOTE_DIR/.git" ]; then
  if [ -z "$REPO_URL" ]; then
    echo "Erro: $REMOTE_DIR nao existe na EC2 e REPO_URL nao foi definido em deploy.env" >&2
    exit 1
  fi
  echo "==> $REMOTE_DIR nao existe ainda, clonando..."
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
)

PARAMS_FILE="$(mktemp)"
trap 'rm -f "$PARAMS_FILE"' EXIT

python3 - "$REMOTE_SCRIPT" > "$PARAMS_FILE" <<'PY'
import json
import sys

script = sys.argv[1]
print(json.dumps({"commands": script.splitlines()}))
PY

echo "==> Publicando branch '$BRANCH' na instância $INSTANCE_ID via SSM..."

COMMAND_ID=$(aws ssm send-command "${AWS_ARGS[@]}" \
  --document-name "AWS-RunShellScript" \
  --instance-ids "$INSTANCE_ID" \
  --timeout-seconds 1800 \
  --parameters "file://$PARAMS_FILE" \
  --query "Command.CommandId" \
  --output text)

echo "==> Command ID: $COMMAND_ID (aguardando conclusão...)"

STATUS="InProgress"
while [ "$STATUS" = "InProgress" ] || [ "$STATUS" = "Pending" ]; do
  sleep 5
  STATUS=$(aws ssm get-command-invocation "${AWS_ARGS[@]}" \
    --command-id "$COMMAND_ID" \
    --instance-id "$INSTANCE_ID" \
    --query "Status" \
    --output text)
done

aws ssm get-command-invocation "${AWS_ARGS[@]}" \
  --command-id "$COMMAND_ID" \
  --instance-id "$INSTANCE_ID" \
  --query "StandardOutputContent" \
  --output text

if [ "$STATUS" != "Success" ]; then
  echo "==> Deploy falhou (status: $STATUS). Erros:" >&2
  aws ssm get-command-invocation "${AWS_ARGS[@]}" \
    --command-id "$COMMAND_ID" \
    --instance-id "$INSTANCE_ID" \
    --query "StandardErrorContent" \
    --output text >&2
  exit 1
fi

echo "==> Deploy concluído."

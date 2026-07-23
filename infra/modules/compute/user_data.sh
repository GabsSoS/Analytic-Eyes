#!/bin/bash
# Bootstrap de INFRAESTRUTURA apenas: instala as ferramentas necessárias
# para rodar a aplicação depois, manualmente. NÃO clona o repositório nem
# sobe o docker-compose.prod.yml - isso continua sendo um passo manual
# (git clone + docker compose up), como já era antes desta automação.
set -euo pipefail

apt-get update -y
apt-get install -y ca-certificates curl gnupg git

# Docker Engine + plugin docker compose (repositório oficial Docker)
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu

# Certbot (Let's Encrypt) - TLS gratuito direto no host, sem ALB.
# A emissao do certificado em si (certbot certonly ...) fica como passo
# manual apos o DNS do dominio apontar para o IP desta instancia (ver
# infra/README.md), ja que o dominio ainda nao esta configurado aqui.
apt-get install -y certbot

#!/bin/bash
# Bootstrap de INFRAESTRUTURA apenas: instala as ferramentas necessárias
# para rodar a aplicação depois, manualmente. NÃO clona o repositório nem
# sobe o docker-compose.prod.yml - isso continua sendo um passo manual
# (git clone + docker compose up), como já era antes desta automação.
set -euo pipefail

# Versoes pinadas conforme disponivel nos repositorios no momento deste
# build (AMI ubuntu-jammy-22.04 / repo oficial da Docker pra jammy). Se um
# boot novo falhar com "Version 'X' for 'pacote' was not found", os
# mirrors avancaram - rode uma instancia ubuntu:22.04 nova, repita os
# passos de apt-get update + add do repo da Docker abaixo, e atualize os
# pins com `apt-cache policy <pacote>` (mesmo procedimento documentado em
# etl-manager/etls/Dockerfile).
apt-get update -y
apt-get install -y \
  ca-certificates=20260601~22.04.1 \
  curl=7.81.0-1ubuntu1.25 \
  gnupg=2.2.27-3ubuntu2.5 \
  git=1:2.34.1-1ubuntu1.17

# Docker Engine + plugin docker compose (repositório oficial Docker)
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y \
  docker-ce=5:29.6.2-1~ubuntu.22.04~jammy \
  docker-ce-cli=5:29.6.2-1~ubuntu.22.04~jammy \
  containerd.io=2.2.6-1~ubuntu.22.04~jammy \
  docker-buildx-plugin=0.35.0-1~ubuntu.22.04~jammy \
  docker-compose-plugin=5.3.1-1~ubuntu.22.04~jammy

systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu

# TLS e responsabilidade do ALB (modules/alb, certificado ACM) - nao precisa
# de Certbot nesta instancia.

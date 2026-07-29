FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Dev roda com bind mount de ./backend:/app (docker-compose-dev.yml) - cria o
# usuario aqui so pra reduzir o impacto de um eventual escape de container;
# quem grava no host de fato e o processo do lado de fora (makemigrations
# roda como root no host tipicamente), o mount nao depende do UID do
# processo dentro do container ser 1000.
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser && \
    chown -R appuser:appuser /app
USER appuser
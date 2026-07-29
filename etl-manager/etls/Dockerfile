FROM python:3.11-slim

WORKDIR /etls

# Copia TODAS as ETLs
COPY . .

# Instala dependências do ODBC para o pyodbc

# Versoes pinadas conforme disponivel nos repositorios no momento deste build
# (base python:3.11-slim / Microsoft apt repo debian/12). Se um rebuild falhar
# com "Version 'X' for 'pacote' was not found", os mirrors avancaram - rode
# `apt-cache policy <pacote>` numa imagem python:3.11-slim nova e atualize os
# pins abaixo.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl=8.14.1-2+deb13u4 \
    gnupg=2.4.7-21+deb13u1 \
    apt-transport-https=3.0.3 \
    build-essential=12.12 \
    unixodbc=2.3.12-2 \
    unixodbc-dev=2.3.12-2 \
 && mkdir -p /etc/apt/keyrings \
 && curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg \
 && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
 && apt-get update \
 && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17=17.11.1.1-1 \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir --upgrade pip \
 && set -e; \
	for f in $(find . -type f -name 'requirements.txt'); do \
		echo "Instalando dependências de $f"; \
		pip install --no-cache-dir --upgrade --force-reinstall -r "$f"; \
	done

# Continua rodando como root de proposito: "/etls" e sempre um bind mount
# do host (arquivos clonados do git ou montados do disco em dev) - forcar
# um usuario nao-root aqui arriscaria um mismatch de UID entre o dono real
# dos arquivos no host e o usuario do container, quebrando a leitura do
# runner.py/scripts das pipelines. Ver docker-compose*.yml (volumes_from /
# bind mount de ./etls).

# Quando o container inicia, executa o runner
ENTRYPOINT ["python", "runner.py"]
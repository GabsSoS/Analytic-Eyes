FROM python:3.11-slim

WORKDIR /etls

# Copia TODAS as ETLs
COPY . .

# Atualiza pip
RUN pip install --upgrade pip

# Instala dependências do ODBC para o pyodbc

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    unixodbc \
    unixodbc-dev \
 && rm -rf /var/lib/apt/lists/*FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
curl \
gnupg \
apt-transport-https \
build-essential \
unixodbc \
unixodbc-dev \
&& mkdir -p /etc/apt/keyrings \
&& curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg \
&& echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
&& apt-get update \
&& ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
&& rm -rf /var/lib/apt/lists/*

# instala dependencia do requirements.txt
RUN set -e; \
	for f in $(find . -type f -name 'requirements.txt'); do \
		echo "Instalando dependências de $f"; \
		pip install --no-cache-dir --upgrade --force-reinstall -r "$f"; \
	done

# Quando o container inicia, executa o runner
ENTRYPOINT ["python", "runner.py"]
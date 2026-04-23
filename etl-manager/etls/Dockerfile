FROM python:3.11-slim

WORKDIR /etls

# Copia TODAS as ETLs
COPY . .

# Atualiza pip
RUN pip install --upgrade pip

# Instala requirements presentes em cada ETL (se houver)
RUN set -e; \
	for f in $(find . -type f -name 'requirements.txt'); do \
		echo "Instalando dependências de $f"; \
		pip install --no-cache-dir --upgrade --force-reinstall -r "$f"; \
	done

# Quando o container inicia, executa o runner
ENTRYPOINT ["python", "runner.py"]
FROM python:3.11-slim

WORKDIR /etls

# Copia TODAS as ETLs
COPY . .

# Instala pip-tools para gerenciar deps (opcional mas recomendado)
RUN pip install --upgrade pip

# Quando o container inicia, executa o runner
ENTRYPOINT ["python", "runner.py"]
# Analytic Eyes

Analytic Eyes é uma plataforma para orquestração e execução de pipelines ETL. O projeto inclui:

- uma API backend em Django (com DRF) em [etl-manager/backend](etl-manager/backend)
- uma interface web em React + Vite em [etl-manager/frontend](etl-manager/frontend)
- um repositório local de ETLs em [etl-manager/etls](etl-manager/etls) e exemplos em [etls/](etls)
- orquestração local via Docker Compose (`etl-manager/docker-compose-dev.yml`) e arquivos de produção

Este README descreve como executar o projeto localmente, arquitetura, endpoints principais e como contribuir.

---

## Sumário

- [Recursos principais](#recursos-principais)
- [Estrutura do repositório](#estrutura-do-repositorio)
- [Requisitos](#requisitos)
- [Executando localmente (desenvolvimento)](#executando-localmente-desenvolvimento)
- [Execução com Docker Compose](#execucao-com-docker-compose)
- [Endpoints e documentação da API](#endpoints-e-documentacao-da-api)
- [Estrutura de uma pipeline (ETL)](#estrutura-de-uma-pipeline-etl)
- [Testes](#testes)
- [Contribuição](#contribuicao)
- [Licença](#licenca)

---

## Recursos principais

- Cadastro, edição e execução assíncrona de pipelines ETL.
- Agendamento recorrente (Celery Beat) e execução por workers (Celery + Docker).
- Controle de permissões: owners e colaboradores com níveis `view`, `execute` e `edit`.
- Documentação OpenAPI (Swagger / ReDoc) disponível quando o backend está em execução.

---

## Estrutura do repositório

- `etl-manager/` — orquestração, Docker Compose e subprojetos:
  - `backend/` — Django app (contém `manage.py`, `requirements.txt`, `config/`);
  - `frontend/` — React + Vite app (código fonte em `src/`);
  - `etls/` — repositório local de ETLs usado pela plataforma;
  # Analytic Eyes

  Analytic Eyes é uma plataforma para orquestração e execução de pipelines ETL. O projeto inclui:

  - uma API backend em Django (com DRF) em `etl-manager/backend`;
  - uma interface web em React + Vite em `etl-manager/frontend`;
  - um repositório local de ETLs em `etl-manager/etls` e exemplos em `etls/`;
  - orquestração local via Docker Compose (`etl-manager/docker-compose-dev.yml`) e arquivos de produção.

  Este README descreve como executar o projeto localmente, arquitetura, endpoints principais e como contribuir.

  ---

  ## Sumário

  - [Recursos principais](#recursos-principais)
  - [Estrutura do repositório](#estrutura-do-repositorio)
  - [Requisitos](#requisitos)
  - [Executando localmente (desenvolvimento)](#executando-localmente-desenvolvimento)
  - [Execução com Docker Compose](#execucao-com-docker-compose)
  - [Endpoints e documentação da API](#endpoints-e-documentacao-da-api)
  - [Estrutura de uma pipeline (ETL)](#estrutura-de-uma-pipeline-etl)
  - [Testes](#testes)
  - [Contribuição](#contribuicao)
  - [Licença](#licenca)

  ---

  ## Recursos principais

  - Cadastro, edição e execução assíncrona de pipelines ETL.
  - Agendamento recorrente (Celery Beat) e execução por workers (Celery + Docker).
  - Controle de permissões: owners e colaboradores com níveis `view`, `execute` e `edit`.
  - Documentação OpenAPI (Swagger / ReDoc) disponível quando o backend está em execução.

  ---

  ## Estrutura do repositório

  - `etl-manager/` — orquestração, Docker Compose e subprojetos:
    - `backend/` — Django app (contém `manage.py`, `requirements.txt`, `config/`);
    - `frontend/` — React + Vite app (código fonte em `src/`);
    - `etls/` — repositório local de ETLs usado pela plataforma;
    - `docker-compose-dev.yml`, `docker-compose.prod.yml`, `nginx` etc.
  - `etls/` — runner e exemplos de ETLs (ex.: `etls/etl_vendas/`).

  ---

  ## Requisitos

  - Docker e Docker Compose (recomendado para desenvolvimento integrado).
  - Python 3.8+ (para desenvolvimento do backend, opcional se usar apenas Docker).
  - Node.js 16+ (para desenvolvimento do frontend, opcional se usar apenas Docker).

  ---

  ## Executando localmente (desenvolvimento)

  Opções: via Docker Compose (recomendado) ou rodando serviços manualmente.

  1) Usando Docker Compose (recomendado)

  ```bash
  cd etl-manager
  docker compose -f docker-compose-dev.yml up --build
  ```

  Após subir, os endpoints padrão são:

  - Frontend: http://localhost:5173
  - Backend (API): http://localhost:8000
  - Swagger: http://localhost:8000/api/docs/

  2) Executando apenas o backend localmente (sem Docker)

  ```bash
  cd etl-manager/backend
  python -m venv .venv
  source .venv/Scripts/activate      # Windows: .venv\Scripts\activate
  pip install -r requirements.txt
  python manage.py migrate
  python manage.py createsuperuser
  python manage.py runserver
  ```

  3) Executando o frontend localmente

  ```bash
  cd etl-manager/frontend
  npm install
  npm run dev
  ```

  Observações:
  - O backend aplica migracões automaticamente quando executado via Docker Compose (conforme configuração atual).
  - Os ETLs persistem em `etl-manager/etls` e são montados nos containers de execução.

  ---

  ## Execução com Docker Compose (produção básica)

  Exemplo mínimo para produção (ajuste variáveis e volumes antes de usar):

  ```bash
  cd etl-manager
  docker compose -f docker-compose.prod.yml up -d --build
  ```

  Recomenda-se usar um registry privado, orquestrador (K8s/Helm/ArgoCD) e gerenciamento de segredos para ambientes reais.

  ---

  ## Endpoints e documentação da API

  Base local: `http://localhost:8000/api/`

  - Login: `POST /api/auth/login/` (retorna token)
  - Me: `GET /api/auth/me/`
  - Pipelines: `GET /api/pipelines/`, `POST /api/pipelines/create/`, `POST /api/pipelines/{id}/` (executar)
  - Runs: `GET /api/pipelines/{id}/runs/`

  Documentação interativa disponível em:

  - Swagger UI: `http://localhost:8000/api/docs/`
  - OpenAPI Schema: `http://localhost:8000/api/schema/`
  - ReDoc: `http://localhost:8000/api/redoc/`

  Consulte os *views* e *urls* em [etl-manager/backend/config/urls.py](etl-manager/backend/config/urls.py).

  ---

  ## Estrutura de uma pipeline (ETL)

  Ao criar uma pipeline via API, a plataforma cria uma pasta em `etl-manager/etls/<nome>/` com arquivos típicos:

  ```text
  main.py
  config.py
  requirements.txt
  .env
  ```

  Para exemplos de ETLs e runner, veja `etls/etl_vendas/` e `etls/runner.py`.

  ---

  ## Testes

  Para executar os testes do backend:

  ```bash
  cd etl-manager/backend
  python -m venv .venv
  source .venv/Scripts/activate
  pip install -r requirements.txt
  python manage.py test
  ```

  Se preferir, execute via Docker Compose (adapte serviços para incluir testes).

  ---

  ## Contribuição

  Contribuições são bem-vindas. Sugestões:

  1. Abra uma issue descrevendo o problema ou melhoria.
  2. Crie um branch com o prefixo `feature/` ou `fix/`.
  3. Abra um Pull Request com descrição clara e passos para testar.

  Recomenda-se seguir o padrão de commits e manter mudanças de infraestrutura em PRs separados.

  ---

  ## Segurança e operação (resumo)

  - Não versionar credenciais; usar mecanismos de secrets em produção.
  - Revisar `ALLOWED_HOSTS`, `CORS` e outras configurações do Django antes do deploy.
  - Proteger acesso ao Docker socket e limitar privilégios dos containers de execução.

  ---

  ## Licença

  Este projeto está licenciado conforme o arquivo [LICENSE](LICENSE).

  ---

  ## Contato

  Para dúvidas: abra uma issue ou entre em contato com os mantenedores do repositório.

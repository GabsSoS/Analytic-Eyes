# Analytic Eyes

O Analytic Eyes e uma plataforma para gerenciamento e orquestracao de pipelines ETL. A aplicacao centraliza o cadastro de fluxos, armazenamento de scripts, controle de permissoes, execucao assíncrona, agendamento recorrente e monitoramento basico de execucoes por meio de uma API REST e uma interface web.

## O que a aplicacao faz

Com o Analytic Eyes, equipes conseguem:

- criar pipelines ETL com codigo Python, dependencias e variaveis de ambiente;
- controlar ownership e compartilhamento entre usuarios com permissoes de visualizacao, execucao e edicao;
- executar pipelines sob demanda de forma assincrona;
- agendar execucoes recorrentes por dia da semana e horario;
- encadear pipelines com gatilhos entre fluxos;
- consultar historico e status das execucoes;
- administrar usuarios e acessar a documentacao interativa da API.

## Arquitetura

O projeto esta organizado em uma stack desacoplada:

- `etl-manager/backend`: API em Django + Django REST Framework.
- `etl-manager/frontend`: interface web em React + Vite.
- `etl-manager/etls`: repositorio local dos scripts ETL executados pela plataforma.
- `Redis`: broker do Celery e controle de locks de execucao.
- `Celery Worker` e `Celery Beat`: processamento assíncrono e disparo de agendamentos.
- `Docker`: isolamento da execucao de cada pipeline.

## Principais recursos da API

### Autenticacao

A autenticacao e baseada em token. O login retorna um token que deve ser enviado no header:

```http
Authorization: Token <seu_token>
```

### Pipelines

A API permite criar, editar, listar, detalhar, executar e excluir pipelines. Cada pipeline pode conter:

- nome e descricao;
- script principal `main.py`;
- `requirements.txt` gerado a partir da lista de bibliotecas;
- arquivo `.env` opcional;
- pipelines ancoradas para disparos encadeados;
- configuracao de agendamento recorrente.

### Permissoes

Cada pipeline possui um owner e pode ser compartilhada com colaboradores usando os niveis:

- `view`
- `execute`
- `edit`

Somente o owner pode:

- transferir ownership;
- alterar colaboradores;
- configurar agendamento;
- excluir a pipeline.

## Documentacao interativa

Com a aplicacao em execucao, a documentacao OpenAPI pode ser acessada em:

- Swagger UI: `http://localhost:8000/api/docs/`
- Schema OpenAPI: `http://localhost:8000/api/schema/`
- ReDoc: `http://localhost:8000/api/redoc/`

## Endpoints da API

Base URL local:

```text
http://localhost:8000/api/
```

### Autenticacao e usuarios

| Metodo | Endpoint | Descricao |
| --- | --- | --- |
| `POST` | `/auth/login/` | Autentica o usuario e retorna token. |
| `GET` | `/auth/me/` | Retorna dados do usuario autenticado. |
| `POST` | `/auth/change-password/` | Altera a senha do usuario autenticado. |
| `POST` | `/users/create/` | Cria um novo usuario. Disponivel apenas para staff. |
| `POST` | `/auth/create-user/` | Alias compativel para criacao de usuario. |
| `GET` | `/users/` | Lista usuarios para selecao de owners e colaboradores. |

### Pipelines

| Metodo | Endpoint | Descricao |
| --- | --- | --- |
| `GET` | `/pipelines/` | Lista as pipelines visiveis ao usuario autenticado. |
| `GET` | `/pipelines/stats/` | Retorna estatisticas resumidas das pipelines acessiveis. |
| `POST` | `/pipelines/create/` | Cria uma nova pipeline ETL. |
| `POST` | `/pipelines/{pipeline_id}/` | Dispara a execucao assíncrona da pipeline. |
| `GET` | `/pipelines/{pipeline_id}/details/` | Retorna detalhes completos da pipeline. |
| `PUT` / `PATCH` | `/pipelines/{pipeline_id}/update/` | Atualiza metadados, codigo, colaboradores, agendamento e owner. |
| `POST` / `DELETE` | `/pipelines/{pipeline_id}/delete/` | Exclui a pipeline mediante confirmacao do nome. |
| `GET` | `/pipelines/{pipeline_id}/runs/` | Consulta o historico de execucoes da pipeline. |
| `GET` / `POST` | `/pipelines/{pipeline_id}/env/` | Consulta ou substitui o arquivo `.env` da pipeline. |

### Infraestrutura e suporte

| Metodo | Endpoint | Descricao |
| --- | --- | --- |
| `GET` | `/health/` | Health check da aplicacao. |

## Exemplos de uso

### 1. Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"admin123\"}"
```

Resposta esperada:

```json
{
  "message": "Login bem-sucedido",
  "token": "seu_token",
  "username": "admin"
}
```

### 2. Criar uma pipeline

```bash
curl -X POST http://localhost:8000/api/pipelines/create/ \
  -H "Authorization: Token seu_token" \
  -F "name=etl_vendas" \
  -F "description=Pipeline de consolidacao de vendas" \
  -F "lib=[\"pandas\",\"requests\"]" \
  -F "main_code=print('Executando pipeline')"
```

Campos aceitos na criacao:

- `name`: nome de exibicao da pipeline.
- `description`: descricao funcional do fluxo.
- `lib`: lista JSON de dependencias Python.
- `main_code`: conteudo do `main.py`.
- `script`: upload opcional de um arquivo `.py`.
- `env`: upload opcional de arquivo `.env`.
- `anchor_pipeline_ids`: lista JSON de pipelines que servem como gatilho.
- `schedule`: objeto JSON com configuracao de agendamento.

Exemplo de `schedule`:

```json
{
  "enabled": true,
  "days_of_week": [1, 3, 5],
  "hour": 8,
  "minute": 30,
  "timezone": "America/Sao_Paulo"
}
```

### 3. Executar uma pipeline

```bash
curl -X POST http://localhost:8000/api/pipelines/1/ \
  -H "Authorization: Token seu_token"
```

Resposta esperada:

```json
{
  "run_id": 12,
  "status": "PENDING"
}
```

## Modelo de execucao

Quando uma pipeline e acionada:

1. a API valida a permissao do usuario;
2. um registro de execucao e criado;
3. o Celery envia a tarefa para processamento assíncrono;
4. o worker executa a ETL em um container Docker isolado;
5. logs e status da execucao ficam associados ao `run`;
6. pipelines ancoradas podem ser disparadas automaticamente ao final da execucao.

## Estrutura esperada de uma pipeline

Cada pipeline criada gera uma pasta em `etl-manager/etls/<nome_normalizado>/` com arquivos como:

```text
main.py
config.py
requirements.txt
.env
```

## Como executar o projeto localmente

### Opcao recomendada: Docker Compose

Na raiz de `etl-manager`, execute:

```bash
docker compose -f docker-compose-dev.yml up --build
```

Servicos principais em ambiente local:

- frontend: `http://localhost:5173`
- backend: `http://localhost:8000`
- swagger: `http://localhost:8000/api/docs/`

### Observacoes sobre o ambiente

- o backend aplica migracoes automaticamente ao subir;
- o worker processa execucoes de pipelines em background;
- o beat verifica agendamentos periodicamente;
- os scripts ETL ficam persistidos na pasta `etl-manager/etls`.

## Requisitos tecnicos

- Docker e Docker Compose
- Python 3 para desenvolvimento local do backend
- Node.js para desenvolvimento local do frontend

## Seguranca e operacao

Alguns cuidados importantes para ambientes reais:

- substituir chaves e credenciais padrao antes de publicar;
- restringir `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` e segredos do Django;
- proteger o acesso ao Docker socket, pois ele concede alto nivel de privilegio ao processo executor;
- usar banco e storage apropriados para producao, conforme a estrategia da equipe.

## Licenca

Este projeto esta licenciado sob os termos definidos em [LICENSE](LICENSE).

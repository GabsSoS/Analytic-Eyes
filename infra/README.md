# Infraestrutura (Terraform) - Analytic Eyes

Provisiona a infraestrutura base de produção: VPC dedicada, ALB (TLS via
ACM) + EC2 privada (host do `docker-compose.prod.yml`, sem IP público),
RDS PostgreSQL (credenciais via AWS Secrets Manager), bucket S3 para
pipelines e a IAM Role que a aplicação usa para acessar Secrets Manager/S3
sem chaves estáticas.

A EC2 fica em subnet privada (sem IP público, sem porta SSH exposta) - o
único ponto de entrada público é o ALB, e mesmo assim restrito aos CIDRs
internos da aplicação (`app_allowed_cidrs`). Acesso administrativo à
instância é via SSM Session Manager, nunca SSH direto. Ver
[Custos e como economizar](#custos-e-como-economizar) antes de aplicar -
este desenho usa NAT Gateway e ALB (diferente de versões anteriores deste
projeto, que evitavam os dois por custo).

Só provisiona infraestrutura - o deploy da aplicação em si (clonar o repo,
`docker compose -f docker-compose.prod.yml up`) continua manual/via
`deploy.sh`, como hoje.

## Estrutura

```
infra/
  bootstrap/        # Aplicar uma única vez: bucket S3 + tabela DynamoDB do remote state
  modules/
    network/         # VPC, 2 subnets públicas (ALB), subnet privada de app (EC2) + NAT, 2 subnets privadas (RDS)
    security/         # Security Groups (ALB, EC2 e RDS)
    s3/               # Bucket novo para pipelines/etls
    rds/              # RDS PostgreSQL, credenciais geradas no Secrets Manager
    iam/              # Role/instance profile da EC2 (Secrets Manager + S3 + SSM)
    compute/          # EC2 (sem IP público) + user_data (Docker/Compose)
    alb/               # ALB + certificado ACM (validação DNS) + target group/listeners
  envs/
    prod/             # Une os módulos acima com o backend remoto (S3+DynamoDB)
```

## Ordem de aplicação

### 1. Bootstrap (uma única vez, por qualquer dev do time)

```bash
cd infra/bootstrap
terraform init
terraform apply
```

Isso cria o bucket S3 e a tabela DynamoDB usados como *remote state* por
`envs/prod`. Se você mudar `state_bucket_name`/`lock_table_name` das
variáveis default, atualize os mesmos valores em `envs/prod/versions.tf`
(o bloco `backend "s3"` não aceita variáveis).

### 2. Ambiente de produção

```bash
cd infra/envs/prod
cp terraform.tfvars.example terraform.tfvars
# edite terraform.tfvars: app_allowed_cidrs, domain_name, domain_alt_names, s3_bucket_name

terraform init
```

O certificado ACM usa validação por DNS (não depende de nenhuma porta
pública da aplicação) - mas como o DNS deste projeto não é gerenciado pelo
Terraform, o apply precisa ser feito em duas etapas:

```bash
# 1) Só o certificado, pra conseguir os registros de validação
terraform apply -target=module.alb.aws_acm_certificate.this
terraform output acm_validation_records

# 2) Adicione os registros CNAME retornados acima no seu provedor de DNS
#    (cada domínio - principal e cada SAN - tem o seu próprio registro).
#    Espere propagar (minutos, às vezes mais).

# 3) Apply completo - fica esperando o ACM validar antes de criar o
#    listener HTTPS, depois cria o resto (ALB, EC2, RDS, etc)
terraform plan   # confira os recursos antes de aplicar - eles custam dinheiro real
terraform apply
```

Ao final, os `outputs` trazem `alb_dns_name`, `ec2_instance_id`,
`db_secret_arn`, `db_name`, `db_endpoint`, `db_port` e `s3_bucket_name`.

Aponte um **CNAME** (ou ALIAS/ANAME, se seu provedor suportar) do seu
domínio para `alb_dns_name` - isso substitui o antigo A record pro IP da
EC2 (a EC2 não tem mais IP público).

O `.env` real (`etl-manager/.env`) usa:

```
DB_SECRET_ARN=<output db_secret_arn>
DB_NAME=<output db_name>
DB_HOST=<output db_endpoint>
DB_PORT=<output db_port>
AWS_STORAGE_BUCKET_NAME=<output s3_bucket_name>
```

**Importante**: o secret gerenciado pela RDS (`manage_master_user_password`)
só contém `{"username": "...", "password": "..."}` - nada de host/port/
dbname. `DB_HOST`/`DB_PORT`/`DB_NAME` são sempre necessários no `.env`,
mesmo com `DB_USE_SECRETS_MANAGER=true` (confirmado rodando em produção -
a suposição inicial de que o secret traria host/port também estava errada).

(`AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` continuam em branco - a EC2 já
tem a IAM Role anexada.)

### 3. Deploy da aplicação

Primeiro deploy (manual, uma única vez - precisa preencher o `.env`). Como
a instância não tem IP público, entre nela via SSM em vez de SSH:

```bash
aws ssm start-session --target <output ec2_instance_id>
# dentro da sessão:
sudo su - ubuntu
git clone <repo> && cd Analytic-Eyes/etl-manager
# preencher .env com os outputs acima
docker compose -f docker-compose.prod.yml up -d --build
```

Depois disso, use `infra/deploy.sh` para publicar atualizações (via SSM Run
Command, clona se `REMOTE_DIR` ainda não existir, senão só dá `git pull` +
rebuild):

```bash
cp infra/deploy.env.example infra/deploy.env   # uma vez, preencha INSTANCE_ID/REPO_URL
./infra/deploy.sh
```

### 4. TLS (ACM)

Já coberto no passo 2 (certificado + registros DNS de validação). O ACM
renova o certificado automaticamente enquanto os registros de validação
continuarem publicados no seu DNS - sem cron, sem Certbot, sem passo manual
recorrente.

## Custos e como economizar

Estimativas em `us-east-1`, sujeitas a mudança - confirme na [calculadora
da AWS](https://calculator.aws) antes de aplicar.

| Recurso | Custo aproximado | Observação |
|---|---|---|
| EC2 t3.medium | ~US$30/mês (on-demand, 24/7) | t3.small (~US$15/mês) travou em produção com o worker do Celery em `CELERY_WORKER_CONCURRENCY=30` - se baixar isso para 2-4 no `.env` da app, t3.small volta a ser viável |
| **NAT Gateway** | **~US$32/mês + processamento** | Necessário pra EC2 privada sair pra internet (Docker Hub/apt/pip/npm) - trade-off aceito pra tirar o IP público da instância |
| **ALB** | **~US$16-25/mês + LCU** | Termina TLS (ACM) e é o único ponto de entrada público - substitui Certbot + IP público na EC2 |
| RDS db.t4g.micro Single-AZ | ~US$0-12/mês | Elegível a free tier em contas novas/elegíveis |
| S3 (bucket pipelines) | Centavos | Só paga o storage real usado |
| Secrets Manager | ~US$0.40/mês | Um secret (o gerenciado pelo RDS) |
| S3 + DynamoDB (state) | Centavos | Uso mínimo |
| Certificado ACM | Grátis | Emissão e renovação não têm custo |

**A maior economia de todas**: como é tudo IaC, rode `terraform destroy` em
`envs/prod` quando não estiver testando, e reaplique (repetindo o passo de
validação do ACM) quando for usar de novo. Entre sessões de teste, só sobra
o bucket S3 + tabela DynamoDB do bootstrap rodando (centavos/mês).

```bash
cd infra/envs/prod
terraform destroy   # derruba tudo (exceto o bootstrap)
```

Quando isto virar produção de verdade (com usuários reais, sem poder ficar
ligando/desligando), revisite: `db_skip_final_snapshot = false`,
`deletion_protection = true`, considerar Multi-AZ no RDS.

## Segurança

- Nenhuma credencial AWS estática em lugar nenhum - a EC2 usa a IAM Role
  criada em `modules/iam`, exatamente como `secrets_manager.py` e
  `pipelines/storage.py` (S3Storage) já esperam.
- RDS sem IP público, só acessível pelo Security Group da EC2.
- **EC2 sem IP público e sem porta SSH exposta** - fica em subnet privada,
  só recebe tráfego do ALB (porta 80, HTTP puro - o TLS já foi terminado no
  ALB). Acesso administrativo é só via SSM Session Manager.
- Aplicação de uso interno: o ALB (HTTP e HTTPS) só aceita conexões dos
  CIDRs em `app_allowed_cidrs` (IP do escritório, IP de saída da VPN
  corporativa) - nunca `0.0.0.0/0`. Diferente do desenho anterior (Certbot
  direto na EC2), a porta 80 do ALB também fica restrita a esses CIDRs,
  porque o ACM valida o certificado via DNS, não via HTTP-01 - não precisa
  mais ficar aberta pra internet.
  - Isso só funciona se a rede de onde as pessoas remotas conectam tiver
    IP de saída fixo/previsível (ex: VPN corporativa **full-tunnel**). Se
    a VPN for split-tunnel, o tráfego para a AWS pode sair pelo IP
    residencial de cada um em vez do IP fixo da VPN, e ficaria bloqueado.
- `terraform.tfvars` é gitignored (contém os CIDRs internos e o domínio) -
  use `terraform.tfvars.example` como referência.

## Acesso administrativo (SSM Session Manager)

A EC2 não tem SSH exposto - todo acesso administrativo é pela IAM Role da
EC2 (policy `AmazonSSMManagedInstanceCore`, `modules/iam/main.tf`), via
console AWS (EC2 → instância → **Connect** → **Session Manager**) ou CLI:

```bash
aws ssm start-session --target <ec2_instance_id>
```

`infra/deploy.sh` usa o mesmo mecanismo (SSM Run Command) para publicar
atualizações sem precisar de SSH.

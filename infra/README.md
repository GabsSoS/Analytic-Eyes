# Infraestrutura (Terraform) - Analytic Eyes

Provisiona a infraestrutura base de produção: VPC dedicada, EC2 (host do
`docker-compose.prod.yml`), RDS PostgreSQL (credenciais via AWS Secrets
Manager), bucket S3 para pipelines e a IAM Role que a aplicação usa para
acessar Secrets Manager/S3 sem chaves estáticas.

Desenhado para o cenário de **teste/validação com custo mínimo**: sem NAT
Gateway, sem ALB, Single-AZ, RDS Postgres comum (não Aurora) no menor
tamanho. Ver [Custos e como economizar](#custos-e-como-economizar) antes de
aplicar.

Só provisiona infraestrutura - o deploy da aplicação em si (clonar o repo,
`docker compose -f docker-compose.prod.yml up`) continua manual, como hoje.

## Estrutura

```
infra/
  bootstrap/        # Aplicar uma única vez: bucket S3 + tabela DynamoDB do remote state
  modules/
    network/         # VPC, subnet pública (EC2) + 2 subnets privadas (RDS)
    security/        # Security Groups (EC2 e RDS)
    s3/               # Bucket novo para pipelines/etls
    rds/              # RDS PostgreSQL, credenciais geradas no Secrets Manager
    iam/              # Role/instance profile da EC2 (Secrets Manager + S3)
    compute/          # EC2 + Elastic IP + user_data (Docker/Compose/certbot)
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
# edite terraform.tfvars: ssh_allowed_cidr, ssh_public_key, s3_bucket_name

terraform init
terraform plan   # confira os recursos antes de aplicar - eles custam dinheiro real
terraform apply
```

Ao final, os `outputs` trazem `ec2_public_ip`, `db_secret_arn`, `db_name` e
`s3_bucket_name` - é isso que vai para o `etl-manager/.env` real:

```
DB_SECRET_ARN=<output db_secret_arn>
DB_NAME=<output db_name>
AWS_STORAGE_BUCKET_NAME=<output s3_bucket_name>
```

(`AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` continuam em branco - a EC2 já
tem a IAM Role anexada.)

### 3. Deploy da aplicação (manual, como hoje)

```bash
ssh -i ~/.ssh/sua-chave ubuntu@<ec2_public_ip>
git clone <repo> && cd Analytic-Eyes/etl-manager
# preencher .env com os outputs acima
docker compose -f docker-compose.prod.yml up -d --build
```

### 4. TLS (Certbot, depois do DNS apontado)

Aponte um A record do seu domínio para `ec2_public_ip` no provedor de DNS
que você já usa hoje (o Terraform não gerencia Route53/DNS - isso ficou
fora do escopo por enquanto). Depois, na EC2:

```bash
sudo certbot certonly --standalone -d seu-dominio.com -d www.seu-dominio.com
```

Configure o nginx (`etl-manager/nginx.conf`) para usar os certificados
gerados e um `listen 443 ssl;`, e agende a renovação (`certbot renew`, o
pacote já registra um timer systemd por padrão). Isso não está automatizado
neste Terraform - é um passo manual, já que o domínio final e o momento de
emissão do certificado dependem de você.

## Custos e como economizar

Estimativas em `us-east-1`, sujeitas a mudança - confirme na [calculadora
da AWS](https://calculator.aws) antes de aplicar.

| Recurso | Custo aproximado | Observação |
|---|---|---|
| EC2 t3.small | ~US$15/mês (on-demand, 24/7) | Pode cair para `t3.micro` para só validar a integração |
| RDS db.t4g.micro Single-AZ | ~US$0-12/mês | Elegível a free tier em contas novas/elegíveis |
| S3 (bucket pipelines) | Centavos | Só paga o storage real usado |
| Secrets Manager | ~US$0.40/mês | Um secret (o gerenciado pelo RDS) |
| S3 + DynamoDB (state) | Centavos | Uso mínimo |
| Elastic IP | Grátis | Só cobra se ficar sem instância associada |
| **NAT Gateway** | **Não usado** | Cortado do desenho - RDS não precisa de saída à internet |
| **ALB** | **Não usado** | TLS feito via Certbot direto na EC2 em vez de ALB+ACM |

**A maior economia de todas**: como é tudo IaC, rode `terraform destroy` em
`envs/prod` quando não estiver testando, e `terraform apply` de novo quando
for usar. Entre sessões de teste, só sobra o bucket S3 + tabela DynamoDB do
bootstrap rodando (centavos/mês) - o resto (EC2, RDS, EIP) some e para de
cobrar.

```bash
cd infra/envs/prod
terraform destroy   # derruba tudo (exceto o bootstrap)
```

Quando isto virar produção de verdade (com usuários reais, sem poder ficar
ligando/desligando), revisite: `db_skip_final_snapshot = false`,
`deletion_protection = true`, considerar Multi-AZ no RDS, e reavaliar
ALB+ACM em vez de Certbot manual.

## Segurança

- Nenhuma credencial AWS estática em lugar nenhum - a EC2 usa a IAM Role
  criada em `modules/iam`, exatamente como `secrets_manager.py` e
  `pipelines/storage.py` (S3Storage) já esperam.
- RDS sem IP público, só acessível pelo Security Group da EC2.
- SSH restrito ao seu IP (`ssh_allowed_cidr`) - nunca abra para `0.0.0.0/0`.
- Aplicação de uso interno: a porta 443 (HTTPS, onde a app é servida de
  verdade) só aceita conexões dos CIDRs em `app_allowed_cidrs` (IP do
  escritório, IP de saída da VPN corporativa). A porta 80 continua aberta
  para `0.0.0.0/0` de propósito - é só o desafio HTTP-01 do Let's
  Encrypt/Certbot (que precisa ser alcançável por IPs arbitrários da
  Let's Encrypt) e o redirect para HTTPS; nenhum conteúdo real da
  aplicação é servido em texto plano ali.
  - Isso só funciona se a rede de onde as pessoas remotas conectam tiver
    IP de saída fixo/previsível (ex: VPN corporativa **full-tunnel**). Se
    a VPN for split-tunnel, o tráfego para a AWS pode sair pelo IP
    residencial de cada um em vez do IP fixo da VPN, e ficaria bloqueado.
- `terraform.tfvars` é gitignored (contém sua chave pública SSH e o CIDR do
  seu IP) - use `terraform.tfvars.example` como referência.

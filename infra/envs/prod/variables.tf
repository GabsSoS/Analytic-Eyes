variable "aws_region" {
  description = "Região AWS onde a infra de prod será criada."
  type        = string
  default     = "us-east-1"
}

variable "name_prefix" {
  description = "Prefixo para nomear todos os recursos deste ambiente."
  type        = string
  default     = "analytic-eyes-prod"
}

variable "azs" {
  description = "Duas AZs da região escolhida (ex: [\"us-east-1a\", \"us-east-1b\"])."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

# --- Acesso ---

variable "app_allowed_cidrs" {
  description = "CIDRs autorizados a acessar a aplicação no ALB (HTTP/HTTPS) (ex: IP da VPN corporativa, IP do escritório). Aplicação de uso interno - nunca inclua 0.0.0.0/0."
  type        = list(string)
}

# --- ALB / ACM ---

variable "domain_name" {
  description = "Domínio principal do certificado ACM/ALB (ex: analytic-eyes.com)."
  type        = string
}

variable "domain_alt_names" {
  description = "Domínios adicionais (SANs), ex: [\"www.analytic-eyes.com\"]."
  type        = list(string)
  default     = []
}

# --- S3 ---

variable "s3_bucket_name" {
  description = "Nome do bucket S3 novo para pipelines (globalmente único, ex: analytic-eyes-pipelines-prod)."
  type        = string
}

# --- RDS ---

variable "db_name" {
  description = "Nome do banco inicial criado na instância RDS (equivalente ao DB_NAME da app Django)."
  type        = string
  default     = "analytic_eyes"
}

variable "db_master_username" {
  description = "Usuário master do banco RDS (a senha é gerada e gerenciada pelo Secrets Manager, nunca aparece aqui)."
  type        = string
  default     = "app_admin"
}

variable "db_instance_class" {
  description = "Classe da instância RDS (ex: db.t4g.micro)."
  type        = string
  default     = "db.t4g.micro"
}

variable "db_skip_final_snapshot" {
  description = "true (padrão) = destroy rápido e sem custo de snapshot, ideal para ambiente de teste. Mude para false quando isto virar produção com dados reais."
  type        = bool
  default     = true
}

# --- EC2 ---

variable "ec2_instance_type" {
  description = "t3.medium (padrão atual): t3.small ficou sem memória com o worker do Celery + backend + redis + nginx no mesmo host e chegou a travar até o SSH. Se quiser voltar a testar com t3.small, baixe antes CELERY_WORKER_CONCURRENCY no .env da app (ex: 2-4 em vez de 30)."
  type        = string
  default     = "t3.medium"
}

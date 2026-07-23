variable "aws_region" {
  type    = string
  default = "us-east-1"
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

variable "ssh_allowed_cidr" {
  description = "Seu IP público em formato CIDR (ex: \"203.0.113.10/32\"). Descubra com: curl -s ifconfig.me"
  type        = string
}

variable "ssh_public_key" {
  description = "Conteúdo da chave pública SSH (cat ~/.ssh/id_ed25519.pub)."
  type        = string
}

variable "app_allowed_cidrs" {
  description = "CIDRs autorizados a acessar a aplicação em HTTPS (ex: IP da VPN corporativa, IP do escritório). Aplicação de uso interno - nunca inclua 0.0.0.0/0."
  type        = list(string)
}

# --- S3 ---

variable "s3_bucket_name" {
  description = "Nome do bucket S3 novo para pipelines (globalmente único, ex: analytic-eyes-pipelines-prod)."
  type        = string
}

# --- RDS ---

variable "db_name" {
  type    = string
  default = "analytic_eyes"
}

variable "db_master_username" {
  type    = string
  default = "app_admin"
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
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

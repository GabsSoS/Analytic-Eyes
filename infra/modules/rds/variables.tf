variable "name_prefix" {
  description = "Prefixo usado no nome dos recursos do RDS (ex: analytic-eyes-prod)."
  type        = string
}

variable "private_subnet_ids" {
  description = "IDs das subnets privadas (>= 2 AZs) para o db_subnet_group."
  type        = list(string)
}

variable "security_group_id" {
  description = "SG que só libera 5432 a partir da EC2 (modules/security)."
  type        = string
}

variable "instance_class" {
  description = "Classe da instância RDS. db.t4g.micro é a mais barata (e costuma cair no free tier em contas elegíveis)."
  type        = string
  default     = "db.t4g.micro"
}

variable "allocated_storage" {
  description = "Storage em GB (gp3). 20GB é o mínimo e cobre o free tier."
  type        = number
  default     = 20
}

variable "engine_version" {
  description = "Versão do PostgreSQL. Confirme versões disponíveis antes de aplicar: aws rds describe-db-engine-versions --engine postgres --query 'DBEngineVersions[].EngineVersion'"
  type        = string
  default     = "16"
}

variable "db_name" {
  description = "Nome do banco inicial criado no cluster (equivalente ao DB_NAME da app Django)."
  type        = string
  default     = "analytic_eyes"
}

variable "master_username" {
  description = "Usuário master do banco (a senha é gerada e gerenciada pelo Secrets Manager, nunca aparece aqui)."
  type        = string
  default     = "app_admin"
}

variable "skip_final_snapshot" {
  description = "true = terraform destroy apaga o banco sem tirar snapshot final. Bom para ambiente de teste (destroy rápido e sem custo de snapshot); mude para false quando isto virar produção de verdade com dados reais."
  type        = bool
  default     = true
}

variable "deletion_protection" {
  description = "Trava exclusão acidental via console/CLI. Deixe false em ambiente de teste para poder destruir livremente."
  type        = bool
  default     = false
}

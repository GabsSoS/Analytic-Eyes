variable "name_prefix" {
  description = "Prefixo usado no nome dos recursos do ALB (ex: analytic-eyes-prod)."
  type        = string
}

variable "vpc_id" {
  description = "ID da VPC (modules/network -> vpc_id)."
  type        = string
}

variable "public_subnet_ids" {
  description = "IDs das >= 2 subnets públicas exigidas pelo ALB (modules/network -> public_subnet_ids)."
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "Security group do ALB (modules/security -> alb_security_group_id)."
  type        = string
}

variable "instance_id" {
  description = "ID da instância EC2 alvo do target group (modules/compute -> instance_id)."
  type        = string
}

variable "domain_name" {
  description = "Domínio principal do certificado ACM (ex: analytic-eyes.com)."
  type        = string
}

variable "domain_alt_names" {
  description = "Domínios adicionais (SANs) do certificado ACM (ex: [\"www.analytic-eyes.com\"])."
  type        = list(string)
  default     = []
}

variable "alb_deletion_protection" {
  description = "Trava exclusão acidental do ALB via console/CLI. Deixe false em ambiente de teste para poder destruir livremente (mesmo padrão de modules/rds.deletion_protection)."
  type        = bool
  default     = false
}

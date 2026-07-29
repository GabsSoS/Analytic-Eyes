variable "name_prefix" {
  description = "Prefixo usado no nome dos security groups (ex: analytic-eyes-prod)."
  type        = string
}

variable "vpc_id" {
  description = "ID da VPC onde os security groups serão criados (modules/network -> vpc_id)."
  type        = string
}

variable "app_allowed_cidrs" {
  description = "CIDRs autorizados a acessar a aplicacao na porta 443 (ex: IP da VPN corporativa, IP do escritorio). Uso interno - nunca 0.0.0.0/0 aqui."
  type        = list(string)
}

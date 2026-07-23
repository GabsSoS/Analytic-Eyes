variable "name_prefix" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "ssh_allowed_cidr" {
  description = "CIDR autorizado a acessar a porta 22 da EC2 (ex: \"SEU_IP/32\"). Nunca use 0.0.0.0/0 aqui."
  type        = string
}

variable "app_allowed_cidrs" {
  description = "CIDRs autorizados a acessar a aplicacao na porta 443 (ex: IP da VPN corporativa, IP do escritorio). Uso interno - nunca 0.0.0.0/0 aqui."
  type        = list(string)
}

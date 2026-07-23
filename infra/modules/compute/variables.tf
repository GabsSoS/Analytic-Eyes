variable "name_prefix" {
  type = string
}

variable "subnet_id" {
  description = "Subnet pública (modules/network -> public_subnet_id)."
  type        = string
}

variable "security_group_id" {
  type = string
}

variable "instance_profile_name" {
  type = string
}

variable "instance_type" {
  description = "t3.small é um ponto de partida seguro (o host roda redis+backend+worker+beat+nginx via docker compose). t3.micro pode servir só para validar a integração com Secrets Manager, sem carga real."
  type        = string
  default     = "t3.small"
}

variable "root_volume_size_gb" {
  type    = number
  default = 20
}

variable "ssh_public_key" {
  description = "Conteúdo da sua chave pública SSH (ex: cat ~/.ssh/id_ed25519.pub). Terraform cria o key pair na AWS a partir disto."
  type        = string
}

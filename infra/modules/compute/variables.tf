variable "name_prefix" {
  description = "Prefixo usado no nome dos recursos de compute (ex: analytic-eyes-prod)."
  type        = string
}

variable "subnet_id" {
  description = "Subnet privada da app (modules/network -> app_subnet_id) - sem IP público."
  type        = string
}

variable "security_group_id" {
  description = "ID do security group da EC2 (modules/security -> ec2_security_group_id)."
  type        = string
}

variable "instance_profile_name" {
  description = "Nome do instance profile IAM anexado à EC2 (modules/iam -> instance_profile_name)."
  type        = string
}

variable "instance_type" {
  description = "t3.small é um ponto de partida seguro (o host roda redis+backend+worker+beat+nginx via docker compose). t3.micro pode servir só para validar a integração com Secrets Manager, sem carga real."
  type        = string
  default     = "t3.small"
}

variable "root_volume_size_gb" {
  description = "Tamanho (GB) do volume raiz (root_block_device) da EC2."
  type        = number
  default     = 20
}

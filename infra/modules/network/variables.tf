variable "name_prefix" {
  description = "Prefixo usado no nome de todos os recursos de rede (ex: analytic-eyes-prod)."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR da VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR da subnet pública (EC2)."
  type        = string
  default     = "10.20.1.0/24"
}

variable "private_subnet_cidr" {
  description = "CIDR da subnet privada (RDS)."
  type        = string
  default     = "10.20.2.0/24"
}

variable "private_subnet_cidr_b" {
  description = "CIDR da segunda subnet privada (RDS exige >= 2 AZs no db_subnet_group, mesmo em Single-AZ)."
  type        = string
  default     = "10.20.3.0/24"
}

variable "azs" {
  description = "Duas Availability Zones a usar (a primeira recebe a subnet pública + privada A, a segunda só a privada B)."
  type        = list(string)
}

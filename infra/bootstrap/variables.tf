variable "aws_region" {
  description = "Região AWS onde o state (S3 + DynamoDB) e a infra de prod vão viver."
  type        = string
  default     = "us-east-1"
}

variable "state_bucket_name" {
  description = "Nome do bucket S3 que guarda o terraform.tfstate. Precisa ser globalmente único."
  type        = string
  default     = "analytic-eyes-tfstate"
}

variable "lock_table_name" {
  description = "Nome da tabela DynamoDB usada para lock do state (evita dois devs aplicarem ao mesmo tempo)."
  type        = string
  default     = "analytic-eyes-tfstate-lock"
}

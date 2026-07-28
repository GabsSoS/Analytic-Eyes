variable "name_prefix" {
  description = "Prefixo usado no nome da role e do instance profile IAM (ex: analytic-eyes-prod)."
  type        = string
}

variable "db_secret_arn" {
  description = "ARN do secret gerenciado pelo RDS (modules/rds -> secret_arn)."
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN do bucket S3 de pipelines (modules/s3 -> bucket_arn)."
  type        = string
}

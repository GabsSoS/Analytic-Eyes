variable "name_prefix" {
  type = string
}

variable "db_secret_arn" {
  description = "ARN do secret gerenciado pelo RDS (modules/rds -> secret_arn)."
  type        = string
}

variable "s3_bucket_arn" {
  description = "ARN do bucket S3 de pipelines (modules/s3 -> bucket_arn)."
  type        = string
}

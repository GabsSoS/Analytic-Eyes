output "ec2_public_ip" {
  description = "Aponte o A record do seu domínio para este IP."
  value       = module.compute.public_ip
}

output "db_secret_arn" {
  description = "Vira DB_SECRET_ARN no etl-manager/.env (produção)."
  value       = module.rds.secret_arn
}

output "db_name" {
  description = "Vira DB_NAME no etl-manager/.env (produção)."
  value       = module.rds.db_name
}

output "db_endpoint" {
  description = "Vira DB_HOST no etl-manager/.env (produção). O secret gerenciado pela RDS só tem username/password - host e port vêm daqui, não do secret."
  value       = module.rds.endpoint
}

output "db_port" {
  description = "Vira DB_PORT no etl-manager/.env (produção)."
  value       = module.rds.port
}

output "s3_bucket_name" {
  description = "Vira AWS_STORAGE_BUCKET_NAME no etl-manager/.env (produção)."
  value       = module.s3.bucket_name
}

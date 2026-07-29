output "alb_dns_name" {
  description = "Aponte um CNAME/ALIAS do seu domínio para este endereço (substitui o antigo A record pro IP da EC2)."
  value       = module.alb.alb_dns_name
}

output "acm_validation_records" {
  description = "Registros CNAME que precisam existir no seu provedor de DNS para o ACM validar o certificado (ver infra/README.md)."
  value       = module.alb.acm_validation_records
}

output "ec2_instance_id" {
  description = "ID da instância EC2 - use com `aws ssm start-session --target` para acesso administrativo (a instância não tem IP público)."
  value       = module.compute.instance_id
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

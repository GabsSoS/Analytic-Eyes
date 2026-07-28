output "endpoint" {
  description = "Endpoint (host) da instância RDS - vira DB_HOST no .env da aplicação."
  value       = aws_db_instance.this.address
}

output "port" {
  description = "Porta da instância RDS - vira DB_PORT no .env da aplicação."
  value       = aws_db_instance.this.port
}

output "db_name" {
  description = "Nome do banco inicial criado na instância RDS."
  value       = aws_db_instance.this.db_name
}

# ARN do secret gerenciado automaticamente pela RDS - é isto que vai virar
# DB_SECRET_ARN no .env da aplicação.
output "secret_arn" {
  description = "ARN do secret gerenciado pela RDS (Secrets Manager) com host/username/password."
  value       = aws_db_instance.this.master_user_secret[0].secret_arn
}

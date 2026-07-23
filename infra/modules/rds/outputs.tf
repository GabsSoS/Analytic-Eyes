output "endpoint" {
  value = aws_db_instance.this.address
}

output "port" {
  value = aws_db_instance.this.port
}

output "db_name" {
  value = aws_db_instance.this.db_name
}

# ARN do secret gerenciado automaticamente pela RDS - é isto que vai virar
# DB_SECRET_ARN no .env da aplicação.
output "secret_arn" {
  value = aws_db_instance.this.master_user_secret[0].secret_arn
}

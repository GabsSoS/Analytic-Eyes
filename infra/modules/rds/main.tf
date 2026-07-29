# RDS PostgreSQL "comum" (não Aurora) - Single-AZ, menor instância possível.
# Aurora Serverless v2 tem piso de custo real (~US$40+/mês mesmo parado);
# um RDS Postgres db.t4g.micro Single-AZ é muito mais barato para um
# ambiente de teste e usa exatamente o mesmo formato de secret gerenciado
# que etl-manager/backend/config/secrets_manager.py já espera. Dá para
# trocar para Aurora depois só neste módulo, sem tocar no código da app.

resource "aws_db_subnet_group" "this" {
  name       = "${var.name_prefix}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "${var.name_prefix}-db-subnet-group"
  }
}

resource "aws_db_instance" "this" {
  identifier     = "${var.name_prefix}-db"
  engine         = "postgres"
  engine_version = var.engine_version
  instance_class = var.instance_class

  allocated_storage = var.allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = var.db_name
  username = var.master_username

  # Gerenciado pela AWS: cria e mantém um secret no Secrets Manager com
  # {username, password, host, port, dbClusterIdentifier, engine, ...}.
  # Nunca definir "password" aqui - é mutuamente exclusivo com esta opção.
  manage_master_user_password = true

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [var.security_group_id]
  publicly_accessible    = false
  multi_az               = false

  # Backup automatico diario + copia as tags do instance pro snapshot -
  # rastro de recuperacao minimo esperado para um cliente regulado (FGC).
  backup_retention_period = var.backup_retention_period
  backup_window           = "03:00-04:00"
  copy_tags_to_snapshot   = true

  # Permite login via token IAM (alem do usuario/senha do Secrets Manager
  # ja usado hoje) - nao substitui o auth atual, so adiciona a opcao.
  iam_database_authentication_enabled = true

  skip_final_snapshot = var.skip_final_snapshot
  deletion_protection = var.deletion_protection
  apply_immediately   = true

  # Exporta logs do engine para o CloudWatch - rastro de auditoria mínimo
  # esperado para um cliente regulado (FGC).
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]

  tags = {
    Name = "${var.name_prefix}-db"
  }
}

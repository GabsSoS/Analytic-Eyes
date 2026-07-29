# Bucket S3 que guarda o terraform.tfstate de envs/prod (e futuros ambientes).
# Custo: centavos/mês (poucos KB de state, sem tráfego relevante).
resource "aws_s3_bucket" "tfstate" {
  bucket = var.state_bucket_name

  # Nunca destrua sem querer - o state é a fonte da verdade de toda a infra.
  lifecycle {
    prevent_destroy = true
  }

  tags = {
    Name = var.state_bucket_name
  }
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket                  = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Bucket dedicado para os logs de acesso do bucket de tfstate - nunca loga
# para si mesmo (evitaria um loop de escrita).
resource "aws_s3_bucket" "tfstate_logs" {
  bucket = "${var.state_bucket_name}-logs"

  tags = {
    Name = "${var.state_bucket_name}-logs"
  }
}

resource "aws_s3_bucket_versioning" "tfstate_logs" {
  bucket = aws_s3_bucket.tfstate_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate_logs" {
  bucket                  = aws_s3_bucket.tfstate_logs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate_logs" {
  bucket = aws_s3_bucket.tfstate_logs.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "tfstate_logs_delivery" {
  statement {
    sid       = "S3ServerAccessLogsPolicy"
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.tfstate_logs.arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["logging.s3.amazonaws.com"]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [aws_s3_bucket.tfstate.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_s3_bucket_policy" "tfstate_logs" {
  bucket = aws_s3_bucket.tfstate_logs.id
  policy = data.aws_iam_policy_document.tfstate_logs_delivery.json
}

resource "aws_s3_bucket_logging" "tfstate" {
  bucket        = aws_s3_bucket.tfstate.id
  target_bucket = aws_s3_bucket.tfstate_logs.id
  target_prefix = "tfstate-access-logs/"
}

# Tabela DynamoDB usada só para lock (evita dois "terraform apply" simultâneos).
# Custo: praticamente zero em modo PAY_PER_REQUEST com o volume de locks de um time pequeno.
resource "aws_dynamodb_table" "tfstate_lock" {
  name         = var.lock_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  # Criptografia com a KMS key gerenciada da AWS (alias/aws/dynamodb) - sem
  # custo adicional de KMS customizada - e PITR pra poder restaurar o state
  # lock table em caso de corrupcao/exclusao acidental.
  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = var.lock_table_name
  }
}

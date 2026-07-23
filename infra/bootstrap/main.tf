# Bucket S3 que guarda o terraform.tfstate de envs/prod (e futuros ambientes).
# Custo: centavos/mês (poucos KB de state, sem tráfego relevante).
resource "aws_s3_bucket" "tfstate" {
  bucket = var.state_bucket_name

  # Nunca destrua sem querer - o state é a fonte da verdade de toda a infra.
  lifecycle {
    prevent_destroy = true
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
}

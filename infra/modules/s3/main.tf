# Bucket novo para pipelines/etls (S3Storage em pipelines/storage.py).
# Privado, versionado, criptografado - custo é só storage real usado
# (poucos MB/GB de scripts e planilhas, praticamente irrelevante).
resource "aws_s3_bucket" "pipelines" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_versioning" "pipelines" {
  bucket = aws_s3_bucket.pipelines.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "pipelines" {
  bucket = aws_s3_bucket.pipelines.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "pipelines" {
  bucket                  = aws_s3_bucket.pipelines.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

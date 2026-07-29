# Bucket novo para pipelines/etls (S3Storage em pipelines/storage.py).
# Privado, versionado, criptografado - custo é só storage real usado
# (poucos MB/GB de scripts e planilhas, praticamente irrelevante).
resource "aws_s3_bucket" "pipelines" {
  bucket = var.bucket_name

  tags = {
    Name = var.bucket_name
  }
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

# Bucket dedicado para os logs de acesso do bucket de pipelines - nunca loga
# para si mesmo (evitaria um loop de escrita).
resource "aws_s3_bucket" "pipelines_logs" {
  bucket = "${var.bucket_name}-logs"

  tags = {
    Name = "${var.bucket_name}-logs"
  }
}

resource "aws_s3_bucket_versioning" "pipelines_logs" {
  bucket = aws_s3_bucket.pipelines_logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "pipelines_logs" {
  bucket                  = aws_s3_bucket.pipelines_logs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "pipelines_logs" {
  bucket = aws_s3_bucket.pipelines_logs.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "pipelines_logs_delivery" {
  statement {
    sid       = "S3ServerAccessLogsPolicy"
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.pipelines_logs.arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["logging.s3.amazonaws.com"]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [aws_s3_bucket.pipelines.arn]
    }
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_s3_bucket_policy" "pipelines_logs" {
  bucket = aws_s3_bucket.pipelines_logs.id
  policy = data.aws_iam_policy_document.pipelines_logs_delivery.json
}

resource "aws_s3_bucket_logging" "pipelines" {
  bucket        = aws_s3_bucket.pipelines.id
  target_bucket = aws_s3_bucket.pipelines_logs.id
  target_prefix = "pipelines-access-logs/"
}

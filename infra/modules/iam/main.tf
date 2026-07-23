# Role anexada à instância EC2 via instance profile - é o que
# etl-manager/backend/config/secrets_manager.py e pipelines/storage.py
# (S3Storage) esperam: boto3 usando a cadeia padrão de credenciais, sem
# nenhuma AWS_ACCESS_KEY_ID/SECRET estática.

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ec2" {
  name               = "${var.name_prefix}-ec2-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_instance_profile" "ec2" {
  name = "${var.name_prefix}-ec2-profile"
  role = aws_iam_role.ec2.name
}

# Permissão mínima: só o secret específico do banco, nunca "secretsmanager:*"
# nem Resource "*". Se o secret usar KMS customizada no futuro, adicionar
# kms:Decrypt restrito a essa key - a key default (aws/secretsmanager) já
# está coberta pela condition kms:ViaService abaixo.
data "aws_iam_policy_document" "secrets" {
  statement {
    sid       = "ReadDbSecret"
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [var.db_secret_arn]
  }

  statement {
    sid       = "DecryptViaSecretsManager"
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["secretsmanager.${data.aws_region.current.name}.amazonaws.com"]
    }
  }
}

data "aws_region" "current" {}

resource "aws_iam_role_policy" "secrets" {
  name   = "${var.name_prefix}-secrets-access"
  role   = aws_iam_role.ec2.id
  policy = data.aws_iam_policy_document.secrets.json
}

# Permissão mínima no bucket de pipelines (mesmas operações que
# pipelines/storage.py:S3Storage já usa: get/put/delete/list/head object).
data "aws_iam_policy_document" "s3" {
  statement {
    sid    = "PipelinesBucketObjects"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = ["${var.s3_bucket_arn}/*"]
  }

  statement {
    sid       = "PipelinesBucketList"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [var.s3_bucket_arn]
  }
}

resource "aws_iam_role_policy" "s3" {
  name   = "${var.name_prefix}-s3-access"
  role   = aws_iam_role.ec2.id
  policy = data.aws_iam_policy_document.s3.json
}

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

  tags = {
    Name = "${var.name_prefix}-ec2-role"
  }
}

resource "aws_iam_instance_profile" "ec2" {
  name = "${var.name_prefix}-ec2-profile"
  role = aws_iam_role.ec2.name

  tags = {
    Name = "${var.name_prefix}-ec2-profile"
  }
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
    resources = [data.aws_kms_alias.secretsmanager.target_key_arn]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["secretsmanager.${data.aws_region.current.name}.amazonaws.com"]
    }
  }
}

data "aws_region" "current" {}

# Resolve o ARN real da KMS key gerenciada pela AWS (alias/aws/secretsmanager)
# pra nunca precisar de Resource = "*" na policy - o Orca aponta Resource "*"
# em kms:Decrypt como risco de exfiltracao mesmo com a condition ViaService.
data "aws_kms_alias" "secretsmanager" {
  name = "alias/aws/secretsmanager"
}

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

# Permite acessar a EC2 via SSM Session Manager (console AWS ou `aws ssm
# start-session`), sem depender da porta 22/SSH. Foi anexada manualmente
# durante um incidente em que o worker do Celery saturou a instância e o
# sshd parou de responder a novas conexões - com essa policy, o Session
# Manager continua funcionando como canal de acesso de emergência mesmo
# quando o SSH não responde (ele não depende de spawnar um processo novo
# via porta 22, usa o agente SSM já residente).
resource "aws_iam_role_policy_attachment" "ssm" {
  role       = aws_iam_role.ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

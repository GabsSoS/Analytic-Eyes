"""Busca credenciais do banco de dados no AWS Secrets Manager.

Usado apenas por config/settings_prod.py. O client boto3 nunca recebe
aws_access_key_id/aws_secret_access_key explicitamente - a autenticação
depende sempre da cadeia padrão de credenciais do boto3 (IAM Role da
instância EC2 em produção), mesmo padrão de fallback já usado por
pipelines/storage.py:S3Storage.
"""
import json
import logging
import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)

_cache = {}


class SecretsManagerConfigError(Exception):
    """Erro ao obter credenciais de banco via AWS Secrets Manager."""


def get_db_credentials(secret_id: str, region_name: str, db_name_env: str = "DB_NAME") -> dict:
    """Busca e valida o secret de credenciais do Aurora, com cache por processo."""
    if secret_id in _cache:
        return _cache[secret_id]

    if not secret_id:
        raise SecretsManagerConfigError(
            "DB_SECRET_ARN não configurado. Defina a env var com o ARN do "
            "secret gerenciado pelo Aurora, ou DB_USE_SECRETS_MANAGER=false "
            "para usar DB_* diretamente (apenas staging/teste)."
        )

    client = boto3.client("secretsmanager", region_name=region_name or None)

    try:
        response = client.get_secret_value(SecretId=secret_id)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "desconhecido")
        raise SecretsManagerConfigError(
            f"Falha ao buscar o secret '{secret_id}' (código={code}). "
            "Verifique: (1) o ARN está correto e o secret existe na região "
            f"'{region_name}'; (2) a IAM role da instância tem permissão "
            "secretsmanager:GetSecretValue para este ARN específico; "
            "(3) se o secret usa uma KMS key customizada, a role também "
            "precisa de kms:Decrypt nessa key."
        ) from exc
    except BotoCoreError as exc:
        raise SecretsManagerConfigError(
            f"Erro de rede/config ao acessar Secrets Manager: {exc}"
        ) from exc

    secret_string = response.get("SecretString")
    if not secret_string:
        raise SecretsManagerConfigError(
            f"Secret '{secret_id}' sem SecretString (formato inesperado)."
        )

    try:
        secret = json.loads(secret_string)
    except json.JSONDecodeError as exc:
        raise SecretsManagerConfigError(
            f"Secret '{secret_id}' não é um JSON válido: {exc}"
        ) from exc

    required = ("username", "password", "host", "port")
    missing = [key for key in required if not secret.get(key)]
    if missing:
        raise SecretsManagerConfigError(
            f"Secret '{secret_id}' não contém as chaves obrigatórias: {missing}."
        )

    dbname = secret.get("dbname") or os.getenv(db_name_env)
    if not dbname:
        raise SecretsManagerConfigError(
            f"Nome do banco não encontrado no secret '{secret_id}' nem na "
            f"env var {db_name_env}. Defina {db_name_env} explicitamente "
            "(secrets gerenciados pela RDS normalmente não incluem dbname)."
        )
    secret["dbname"] = dbname

    _cache[secret_id] = secret
    return secret

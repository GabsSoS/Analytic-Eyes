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


def get_db_credentials(
    secret_id: str,
    region_name: str,
    db_name_env: str = "DB_NAME",
    db_host_env: str = "DB_HOST",
    db_port_env: str = "DB_PORT",
) -> dict:
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

    required = ("username", "password")
    missing = [key for key in required if not secret.get(key)]
    if missing:
        raise SecretsManagerConfigError(
            f"Secret '{secret_id}' não contém as chaves obrigatórias: {missing}."
        )

    # O secret "master user password" gerenciado pela RDS só traz
    # username/password - host, port e dbname não fazem parte dele (são
    # fatos de infraestrutura, não credenciais que giram). Resolve a
    # partir de env vars separadas, preenchidas com os outputs do Terraform
    # (module.rds.endpoint / .port / .db_name).
    dbname = secret.get("dbname") or os.getenv(db_name_env)
    if not dbname:
        raise SecretsManagerConfigError(
            f"Nome do banco não encontrado no secret '{secret_id}' nem na "
            f"env var {db_name_env}. Defina {db_name_env} explicitamente "
            "(secrets gerenciados pela RDS normalmente não incluem dbname)."
        )
    secret["dbname"] = dbname

    host = secret.get("host") or os.getenv(db_host_env)
    if not host:
        raise SecretsManagerConfigError(
            f"Host do banco não encontrado no secret '{secret_id}' nem na "
            f"env var {db_host_env}. Defina {db_host_env} explicitamente "
            "(secrets gerenciados pela RDS normalmente não incluem host)."
        )
    secret["host"] = host

    port = secret.get("port") or os.getenv(db_port_env)
    if not port:
        raise SecretsManagerConfigError(
            f"Porta do banco não encontrada no secret '{secret_id}' nem na "
            f"env var {db_port_env}. Defina {db_port_env} explicitamente "
            "(secrets gerenciados pela RDS normalmente não incluem port)."
        )
    secret["port"] = port

    _cache[secret_id] = secret
    return secret

import os

from django.core.exceptions import ImproperlyConfigured

from .settings import *
from .secrets_manager import SecretsManagerConfigError, get_db_credentials


DEBUG = False

SECRET_KEY = os.getenv("SECRET_KEY", SECRET_KEY)

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "ALLOWED_HOSTS",
        "analytic-eyes.com,www.analytic-eyes.com,localhost,127.0.0.1",
    ).split(",")
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CSRF_TRUSTED_ORIGINS",
        "https://analytic-eyes.com,https://www.analytic-eyes.com,http://localhost,http://127.0.0.1",
    ).split(",")
    if origin.strip()
]

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "https://analytic-eyes.com,https://www.analytic-eyes.com,http://localhost,http://127.0.0.1",
    ).split(",")
    if origin.strip()
]

# Banco de dados: Aurora PostgreSQL. Por padrão, credenciais vêm do secret
# gerenciado pela RDS no AWS Secrets Manager (DB_SECRET_ARN). Definir
# DB_USE_SECRETS_MANAGER=false para usar DB_* diretamente (staging/teste
# sem Secrets Manager configurado) - nunca é um fallback automático de erro.
DB_USE_SECRETS_MANAGER = os.getenv("DB_USE_SECRETS_MANAGER", "true").lower() == "true"

if DB_USE_SECRETS_MANAGER:
    try:
        db_creds = get_db_credentials(
            secret_id=os.getenv("DB_SECRET_ARN"),
            region_name=AWS_S3_REGION_NAME,
        )
    except SecretsManagerConfigError as exc:
        raise ImproperlyConfigured(str(exc)) from exc

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_creds["dbname"],
            "USER": db_creds["username"],
            "PASSWORD": db_creds["password"],
            "HOST": db_creds["host"],
            "PORT": str(db_creds["port"]),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }

STATIC_URL = "/static/"
STATIC_ROOT = os.getenv("STATIC_ROOT", str(BASE_DIR / "staticfiles"))

MEDIA_URL = "/media/"
MEDIA_ROOT = os.getenv("MEDIA_ROOT", str(BASE_DIR / "media"))

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

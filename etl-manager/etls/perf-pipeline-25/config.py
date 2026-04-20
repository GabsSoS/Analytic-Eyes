import os

API_VENDAS_URL = os.getenv("API_VENDAS_URL", "http://api.vendas.com")
DB_CONNECTION = os.getenv("DB_CONNECTION", "sqlite:///vendas.db")

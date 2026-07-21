import os

API_PIPELINE_URL = os.getenv("API_PIPELINE_URL", "http://api.pipeline.com")
DB_CONNECTION = os.getenv("DB_CONNECTION", "sqlite:///pipeline.db")

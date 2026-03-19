"""
backend/app/core/config.py
Loads all environment variables from .env file.
"""

import os
from dotenv import load_dotenv

# Load .env file from the backend root directory
load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # Frontend URL for CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # Azure Content Understanding
    AZURE_CU_ENDPOINT: str = os.getenv("AZURE_CU_ENDPOINT", "")
    AZURE_CU_KEY: str = os.getenv("AZURE_CU_KEY", "")
    AZURE_CU_ANALYZER_ID: str = os.getenv("AZURE_CU_ANALYZER_ID", "")

    # TODO: set these variables before running — see backend/.env.example


settings = Settings()

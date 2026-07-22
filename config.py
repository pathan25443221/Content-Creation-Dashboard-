import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

class Settings:
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'content_dashboard.db'}")

    # Local AI / Ollama Configuration
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

    # YouTube API Configuration
    YOUTUBE_CLIENT_SECRETS_FILE: str = os.getenv(
        "YOUTUBE_CLIENT_SECRETS_FILE", 
        str(BASE_DIR / "publisher" / "credentials" / "youtube_client_secret.json")
    )
    YOUTUBE_OAUTH_TOKEN_FILE: str = os.getenv(
        "YOUTUBE_OAUTH_TOKEN_FILE", 
        str(BASE_DIR / "publisher" / "credentials" / "youtube_token.json")
    )

    # Instagram API Configuration
    INSTAGRAM_APP_ID: str = os.getenv("INSTAGRAM_APP_ID", "")
    INSTAGRAM_APP_SECRET: str = os.getenv("INSTAGRAM_APP_SECRET", "")
    INSTAGRAM_ACCESS_TOKEN: str = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    INSTAGRAM_BUSINESS_ACCOUNT_ID: str = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")

# Single instance exported across the application
settings = Settings()

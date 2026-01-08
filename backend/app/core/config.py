import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file ONLY for local development
# Cloud Run sets environment variables directly, so we skip .env loading there
ROOT_DIR = Path(__file__).parent.parent.parent
IS_CLOUD_RUN = os.path.exists("/workspace")

if not IS_CLOUD_RUN:
    # Local development: load .env file
    load_dotenv(ROOT_DIR / '.env', override=False)
else:
    # Cloud Run: use environment variables directly, do NOT load .env
    print("🌐 Running on Cloud Run - using environment variables directly (not loading .env file)")

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Ship Management System API"
    VERSION: str = "2.0.0"
    
    # Security
    JWT_SECRET: str = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
    JWT_ALGORITHM: str = 'HS256'
    JWT_EXPIRATION_HOURS: int = 24
    
    # Database
    MONGO_URL: str = os.getenv('MONGO_URL', '')
    DB_NAME: str = os.getenv('DB_NAME', 'ship_management')
    
    # AI
    EMERGENT_LLM_KEY: Optional[str] = os.getenv('EMERGENT_LLM_KEY')
    GOOGLE_AI_API_KEY: Optional[str] = os.getenv('GOOGLE_AI_API_KEY')  # For direct Google API on Cloud Run
    
    # Admin Initialization (Auto-create admin on first startup)
    INIT_ADMIN_USERNAME: str = os.getenv('INIT_ADMIN_USERNAME', 'system_admin')
    INIT_ADMIN_EMAIL: str = os.getenv('INIT_ADMIN_EMAIL', 'admin@company.com')
    INIT_ADMIN_PASSWORD: Optional[str] = os.getenv('INIT_ADMIN_PASSWORD')
    INIT_ADMIN_FULL_NAME: str = os.getenv('INIT_ADMIN_FULL_NAME', 'System Administrator')
    
    # Paths
    UPLOAD_DIR: Path = ROOT_DIR / "uploads"
    
    class Config:
        case_sensitive = True

settings = Settings()

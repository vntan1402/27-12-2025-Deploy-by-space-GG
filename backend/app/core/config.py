import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Detect if running on Cloud Run
# Cloud Run sets K_SERVICE, K_REVISION, K_CONFIGURATION environment variables
IS_CLOUD_RUN = bool(os.environ.get('K_SERVICE') or os.environ.get('K_REVISION') or os.path.exists("/workspace"))

# Load environment variables from .env file ONLY for local development
# Cloud Run sets environment variables directly, so we skip .env loading there
ROOT_DIR = Path(__file__).parent.parent.parent

if not IS_CLOUD_RUN:
    # Local development: load .env file
    env_path = ROOT_DIR / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=False)
        print(f"📁 Loaded .env file from {env_path}")
    else:
        print(f"⚠️ No .env file found at {env_path}")
else:
    # Cloud Run: use environment variables directly, do NOT load .env
    print("🌐 Running on Cloud Run - using environment variables directly (not loading .env file)")
    print(f"   K_SERVICE: {os.environ.get('K_SERVICE', 'not set')}")
    print(f"   K_REVISION: {os.environ.get('K_REVISION', 'not set')}")

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

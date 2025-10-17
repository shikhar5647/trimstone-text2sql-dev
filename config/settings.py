"""Application configuration settings."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings."""
    
    # Gemini Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    
    # Database Configuration (pymssql format)
    DB_SERVER: str = os.getenv("DB_SERVER", "trimstone-dev.database.windows.net")
    DB_DATABASE: str = os.getenv("DB_DATABASE", "trimstone")
    DB_USERNAME: str = os.getenv("DB_USERNAME", "trimstone")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    
    # Application Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))
    
    # Project Root
    PROJECT_ROOT: Path = Path(__file__).parent.parent

settings = Settings()
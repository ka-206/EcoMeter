import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ecometer.db")
CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if origin.strip()]

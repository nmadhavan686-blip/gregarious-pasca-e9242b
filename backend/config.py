import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "c2t_mobiles_default_secret_key_2026")
    DATABASE_PATH = BASE_DIR / "database" / "c2t_mobiles.db"
    SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"
    UPLOADS_DIR = BASE_DIR / "uploads" / "products"
    
    OWNER_WHATSAPP_NUMBER = os.getenv("OWNER_WHATSAPP_NUMBER", "919994645492").strip()
    OWNER_EMAIL = os.getenv("OWNER_EMAIL", "Cyber2tech.official@gmail.com").strip()
    OWNER_PASSWORD = os.getenv("OWNER_PASSWORD", "").strip()
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    
    BUSINESS_NAME = os.getenv("BUSINESS_NAME", "C2T MOBILES")
    BUSINESS_EMAIL = os.getenv("BUSINESS_EMAIL", "contact@c2tmobiles.com")
    INSTAGRAM_URL = os.getenv("INSTAGRAM_URL", "https://instagram.com/c2tmobiles")
    YOUTUBE_URL = os.getenv("YOUTUBE_URL", "https://youtube.com/@c2tmobiles")
    BUSINESS_ADDRESS = os.getenv("BUSINESS_ADDRESS", "")
    PRODUCTION_APP_URL = os.getenv("PRODUCTION_APP_URL", "https://c2tmobiles.com")
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size

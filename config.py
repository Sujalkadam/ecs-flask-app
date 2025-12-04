import os
from pathlib import Path
from dotenv import load_dotenv

# ------------------------------------------------------
# ALWAYS TRY TO LOAD .env (local or EC2 or Docker)
# ------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# ------------------------------------------------------
# DETECT ENV (default = development)
# ------------------------------------------------------
FLASK_ENV = os.getenv("FLASK_ENV", "development")

# ------------------------------------------------------
# CONFIG CLASS
# ------------------------------------------------------
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")

    # Local defaults (dev)
    DEFAULT_USER = "root"
    DEFAULT_PASS = ""
    DEFAULT_HOST = "127.0.0.1"
    DEFAULT_PORT = "3306"
    DEFAULT_DB   = "inventory"

    MYSQL_USER = os.getenv("MYSQL_USER", DEFAULT_USER)
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", DEFAULT_PASS)
    MYSQL_HOST = os.getenv("MYSQL_HOST", DEFAULT_HOST)
    MYSQL_PORT = os.getenv("MYSQL_PORT", DEFAULT_PORT)
    MYSQL_DB = os.getenv("MYSQL_DB", DEFAULT_DB)

    # Build the final DB URI
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}

def get_config():
    return config_map.get(FLASK_ENV, DevelopmentConfig)


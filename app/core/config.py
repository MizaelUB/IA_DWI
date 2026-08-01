import os
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cargar .env y mailer/.env
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
load_dotenv(os.path.join(PROJECT_ROOT, "mailer", ".env"))

DB_DIR = os.path.join(PROJECT_ROOT, "db")
DOTENV_PATH = os.path.join(PROJECT_ROOT, ".env")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
VECTOR_DB_DIR = os.path.join(PROJECT_ROOT, "mi_base_vectorial")
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")

# Configuración del Mailer
MAILER_EMAIL = os.getenv("MAILER_EMAIL", "")
APP_PASSWORD = os.getenv("APP_PASSWORD", "")

import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_DIR = os.path.join(PROJECT_ROOT, "db")
DOTENV_PATH = os.path.join(PROJECT_ROOT, ".env")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
VECTOR_DB_DIR = os.path.join(PROJECT_ROOT, "mi_base_vectorial")
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")

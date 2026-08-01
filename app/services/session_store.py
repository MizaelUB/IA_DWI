import os
import sqlite3
from typing import List, Dict

from app.core.config import DB_DIR
DB_PATH = os.path.join(DB_DIR, "sessions.db")

def inicializar_db():
    os.makedirs(DB_DIR, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        try:
            cursor.execute("ALTER TABLE chat_messages ADD COLUMN veterinary_id INTEGER")
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("ALTER TABLE chat_messages ADD COLUMN user_id INTEGER")
        except sqlite3.OperationalError:
            pass
            
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversation_id ON chat_messages(conversation_id)")
        cursor.execute("DELETE FROM chat_messages WHERE role NOT IN ('user', 'assistant')")
        conn.commit()
    
    inicializar_tablas_registro()

def obtener_historial(conversation_id: str, user_id: int | None = None) -> List[Dict[str, str]]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if user_id is not None:
            cursor.execute(
                "SELECT role, content FROM chat_messages WHERE conversation_id = ? AND user_id = ? ORDER BY id ASC",
                (conversation_id, user_id)
            )
        else:
            cursor.execute(
                "SELECT role, content FROM chat_messages WHERE conversation_id = ? ORDER BY id ASC",
                (conversation_id,)
            )
        return [{"role": row["role"], "content": row["content"]} for row in cursor.fetchall()]


def verificar_propiedad_conversacion(conversation_id: str, user_id: int | None) -> bool:
    if not conversation_id or user_id is None:
        return False
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id FROM chat_messages WHERE conversation_id = ? AND user_id IS NOT NULL LIMIT 1",
            (conversation_id,)
        )
        row = cursor.fetchone()
        if not row:
            return False
        return row[0] == user_id


def guardar_mensaje(conversation_id: str, role: str, content: str, veterinary_id: int | None = None, user_id: int | None = None):
    if role not in ("user", "assistant"):
        return
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO chat_messages (conversation_id, role, content, veterinary_id, user_id) VALUES (?, ?, ?, ?, ?)",
            (conversation_id, role, content, veterinary_id, user_id)
        )
        conn.commit()

def obtener_veterinary_id_de_sesion(conversation_id: str) -> int | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT veterinary_id FROM chat_messages WHERE conversation_id = ? AND veterinary_id IS NOT NULL LIMIT 1",
            (conversation_id,)
        )
        row = cursor.fetchone()
        return row["veterinary_id"] if row else None

def obtener_conversacion_activa(veterinary_id: int, user_id: int) -> str | None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT conversation_id 
            FROM chat_messages 
            WHERE veterinary_id = ? AND user_id = ? 
            ORDER BY id DESC 
            LIMIT 1
            """,
            (veterinary_id, user_id)
        )
        row = cursor.fetchone()
        return row["conversation_id"] if row else None

def eliminar_historial(conversation_id: str, user_id: int | None = None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        if user_id is not None:
            cursor.execute("DELETE FROM chat_messages WHERE conversation_id = ? AND user_id = ?", (conversation_id, user_id))
        else:
            cursor.execute("DELETE FROM chat_messages WHERE conversation_id = ?", (conversation_id,))
        conn.commit()

def eliminar_historial_por_sesion(veterinary_id: int, user_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_messages WHERE veterinary_id = ? AND user_id = ?", (veterinary_id, user_id))
        conn.commit()


# ============================================================
# Tablas de Registro de Usuarios y Veterinarias Pendientes
# ============================================================

def inicializar_tablas_registro():
    """Crea las tablas de usuarios registrados y solicitudes de veterinaria."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registered_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                full_name TEXT NOT NULL,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS veterinary_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                vet_name TEXT NOT NULL,
                vet_city TEXT NOT NULL,
                vet_address TEXT,
                vet_phone TEXT,
                vet_email TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES registered_users(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verification_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                code TEXT NOT NULL,
                purpose TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                is_verified INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def crear_usuario(username: str, password_hash: str, email: str, full_name: str, phone: str) -> int | None:
    """Crea un usuario registrado. Retorna el ID o None si ya existe."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO registered_users (username, password, email, full_name, phone) VALUES (?, ?, ?, ?, ?)",
                (username, password_hash, email, full_name, phone)
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None


def crear_solicitud_veterinaria(user_id: int, vet_name: str, vet_city: str, vet_address: str, vet_phone: str, vet_email: str) -> int:
    """Crea una solicitud de veterinaria pendiente de aprobación."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO veterinary_requests (user_id, vet_name, vet_city, vet_address, vet_phone, vet_email) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, vet_name, vet_city, vet_address, vet_phone, vet_email)
        )
        conn.commit()
        return cursor.lastrowid


def obtener_usuario_por_username(username: str) -> dict | None:
    """Obtiene un usuario registrado por su username."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registered_users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def obtener_usuario_por_email(email: str) -> dict | None:
    """Obtiene un usuario registrado por su email."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registered_users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def obtener_solicitud_veterinaria(user_id: int) -> dict | None:
    """Obtiene la solicitud de veterinaria más reciente de un usuario."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM veterinary_requests WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def obtener_usuario_por_id(user_id: int) -> dict | None:
    """Obtiene un usuario registrado por su ID."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM registered_users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


# ============================================================
# Manejo de Códigos de Verificación (Registro y Recuperación)
# ============================================================

def guardar_codigo_verificacion(email: str, code: str, purpose: str, expires_in_minutes: int = 15):
    """Guarda un nuevo código de verificación desactivando anteriores del mismo propósito."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Eliminar o desactivar viejos códigos para el mismo correo y propósito
        cursor.execute(
            "DELETE FROM verification_codes WHERE email = ? AND purpose = ?",
            (email, purpose)
        )
        cursor.execute(
            """
            INSERT INTO verification_codes (email, code, purpose, expires_at, is_verified)
            VALUES (?, ?, ?, datetime('now', ?), 0)
            """,
            (email, code, purpose, f"+{expires_in_minutes} minutes")
        )
        conn.commit()


def verificar_codigo(email: str, code: str, purpose: str) -> bool:
    """Verifica si el código es correcto y no ha expirado. Si es válido, lo marca como verificado."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id FROM verification_codes 
            WHERE email = ? AND code = ? AND purpose = ? 
              AND is_verified = 0 
              AND datetime(expires_at) > datetime('now')
            ORDER BY id DESC LIMIT 1
            """,
            (email, code, purpose)
        )
        row = cursor.fetchone()
        if row:
            code_id = row[0]
            cursor.execute("UPDATE verification_codes SET is_verified = 1 WHERE id = ?", (code_id,))
            conn.commit()
            return True
        return False


def esta_email_verificado(email: str, purpose: str) -> bool:
    """Revisa si un email tiene una verificación válida activa (marcada como is_verified = 1 y no expirada)."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id FROM verification_codes 
            WHERE email = ? AND purpose = ? AND is_verified = 1
              AND datetime(expires_at) > datetime('now')
            ORDER BY id DESC LIMIT 1
            """,
            (email, purpose)
        )
        return cursor.fetchone() is not None


def consumir_verificacion_email(email: str, purpose: str):
    """Elimina las verificaciones consumidas para que no se puedan reutilizar."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM verification_codes WHERE email = ? AND purpose = ?",
            (email, purpose)
        )
        conn.commit()


def actualizar_password_usuario(email: str, password_hash: str) -> bool:
    """Actualiza la contraseña de un usuario a partir de su correo."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE registered_users SET password = ? WHERE email = ?",
            (password_hash, email)
        )
        conn.commit()
        return cursor.rowcount > 0


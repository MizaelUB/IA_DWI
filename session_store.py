import os
import sqlite3
from typing import List, Dict

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db")
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


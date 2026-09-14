import sqlite3
import os
from typing import List, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "agent_memory.db")


def init_db():
    """Inicializa la tabla de memoria si no existe."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            plan TEXT,
            code TEXT,
            is_approved BOOLEAN,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_task_memory(task: str, plan: str, code: str, is_approved: bool):
    """Guarda el resultado de una tarea en la base de datos de memoria."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO task_history (task, plan, code, is_approved) VALUES (?, ?, ?, ?)",
        (task, plan, code, is_approved)
    )
    conn.commit()
    conn.close()


def get_recent_history(limit: int = 3) -> List[Dict[str, Any]]:
    """Obtiene el historial reciente de tareas ejecutadas."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT task, plan, code, is_approved FROM task_history ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()

    return [
        {"task": r[0], "plan": r[1], "code": r[2], "is_approved": bool(r[3])}
        for r in rows
    ]
import os
import redis
import psycopg2
from pymongo import MongoClient


POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://devuser:devpassword@postgres:5432/devagents_db")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongodb:27017/devagents_nosql")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))


redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)


mongo_client = MongoClient(MONGO_URL)
mongo_db = mongo_client["devagents_nosql"]
agent_logs_collection = mongo_db["agent_execution_logs"]


def init_postgres():
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_executions (
                id SERIAL PRIMARY KEY,
                task_id VARCHAR(100),
                status VARCHAR(50),
                iterations INT DEFAULT 0,
                is_approved BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("[DB] PostgreSQL initialized successfully.")
    except Exception as e:
        print(f"[DB Warning] Error initiating PostgreSQL: {e}")

def save_task_metrics_pg(task_id: str, status: str, iterations: int, is_approved: bool):
    try:
        conn = psycopg2.connect(POSTGRES_URL)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO task_executions (task_id, status, iterations, is_approved)
            VALUES (%s, %s, %s, %s);
        """, (task_id, status, iterations, is_approved))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[DB Warning] Failed to save metrics in PostgreSQL: {e}")

def save_full_trace_mongo(task_id: str, final_state: dict):
    try:
        agent_logs_collection.insert_one({
            "task_id": task_id,
            "final_state": final_state
        })
    except Exception as e:
        print(f"[DB Warning] Failed to save trace in MongoDB: {e}")
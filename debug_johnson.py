import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

def debug_johnson():
    print("--- Searching SQL Database ---")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("--- Searching 'employees' for logistics ---")
    cur.execute("SELECT user_id, tenant_id, org_id FROM employees WHERE user_id LIKE '%logistics%' LIMIT 10")
    rows = cur.fetchall()
    for row in rows:
        print(row)
    cur.close()
    conn.close()

if __name__ == "__main__":
    debug_johnson()

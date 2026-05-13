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
    print("--- Listing Managers (High-Level Access) ---")
    cur.execute("SELECT user_id, tenant_id, org_id FROM users WHERE 'manager' = ANY(roles) LIMIT 10")
    rows = cur.fetchall()
    print("USER_ID | TENANT | ORG")
    for row in rows:
        print(f"{row[0]} | {row[1]} | {row[2]}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    debug_johnson()

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
    print("--- Searching 'users' table for acme_sales ---")
    cur.execute("SELECT user_id, tenant_id, org_id FROM users WHERE user_id LIKE 'acme_sales%' LIMIT 10")
    rows = cur.fetchall()
    for row in rows:
        print(row)
    
    if not rows:
        print("No acme_sales users found. Listing all acme users:")
        cur.execute("SELECT user_id FROM users WHERE tenant_id='acme' LIMIT 5")
        print(cur.fetchall())
    cur.close()
    conn.close()

if __name__ == "__main__":
    debug_johnson()

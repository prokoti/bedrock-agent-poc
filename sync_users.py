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

def sync_users():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("--- Syncing Users from Employees Table ---")
    
    # 1. Identify employees who don't have a user account yet
    cur.execute("""
        INSERT INTO users (user_id, tenant_id, org_id, roles, sub_ids, classification_access, eligibility_context)
        SELECT 
            e.user_id, 
            e.tenant_id, 
            e.org_id, 
            ARRAY['analyst']::text[],   -- Default role
            ARRAY[e.org_id]::text[],    -- Default sub-access
            ARRAY['confidential']::text[], -- Default classification
            ARRAY['enabled']::text[]      -- Default eligibility
        FROM employees e
        LEFT JOIN users u ON e.user_id = u.user_id
        WHERE u.user_id IS NULL
    """)
    
    count = cur.rowcount
    conn.commit()
    
    print(f"✅ Success! Created {count} new security accounts.")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    sync_users()

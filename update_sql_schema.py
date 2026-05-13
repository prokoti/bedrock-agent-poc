import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# DB Configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

def update_schema():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("--- Updating SQL Schema ---")
        
        # Helper to add column if it doesn't exist
        def add_column_if_not_exists(table, column, col_type):
            try:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                print(f"Added column '{column}' to table '{table}'.")
            except psycopg2.errors.DuplicateColumn:
                conn.rollback()
                print(f"Column '{column}' already exists in table '{table}'.")
            except Exception as e:
                conn.rollback()
                print(f"Error adding {column} to {table}: {e}")

        # Update Employees table
        add_column_if_not_exists("employees", "tenant_id", "VARCHAR(50) DEFAULT 'acme'")
        add_column_if_not_exists("employees", "org_id", "VARCHAR(50) DEFAULT 'engineering'")
        add_column_if_not_exists("employees", "user_id", "VARCHAR(50) DEFAULT 'user_1'")
        
        # Update Projects table
        add_column_if_not_exists("projects", "tenant_id", "VARCHAR(50) DEFAULT 'acme'")
        add_column_if_not_exists("projects", "org_id", "VARCHAR(50) DEFAULT 'engineering'")
        add_column_if_not_exists("projects", "user_id", "VARCHAR(50) DEFAULT 'user_1'")

        # Create Users table for Production Identity Registry
        print("\n--- Creating User Permission Registry ---")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR(50) PRIMARY KEY,
                tenant_id VARCHAR(50) NOT NULL,
                org_id VARCHAR(50) NOT NULL,
                sub_ids TEXT[] NOT NULL,
                roles TEXT[] NOT NULL,
                classification_access TEXT[] NOT NULL,
                eligibility_context VARCHAR(20) DEFAULT 'enabled'
            )
        """)

        # Update some existing data to have variety
        print("\n--- Updating Sample Data for Diversity ---")
        cur.execute("UPDATE employees SET org_id = 'sales', user_id = 'user_2' WHERE id % 2 = 0")
        cur.execute("UPDATE projects SET org_id = 'marketing', tenant_id = 'globex' WHERE budget > 50000")
        
        conn.commit()
        cur.close()
        conn.close()
        print("\nSUCCESS: SQL Tables Updated Successfully.")
        
    except Exception as e:
        print(f"FAILED to update SQL schema: {str(e)}")

if __name__ == "__main__":
    update_schema()

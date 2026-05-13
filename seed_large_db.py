import psycopg2
import os
import random
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

TENANTS = ["acme", "globex", "initech", "umbrella", "hooli"]
ORGS = ["logistics", "warehouse", "capital", "research", "hq", "sales", "ops"]
POSITIONS = ["Engineer", "Manager", "Analyst", "Lead", "Architect", "Scientist"]
PROJECT_STATUS = ["Active", "Completed", "On Hold", "Planning"]

FIRST_NAMES = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"]

def seed_database():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("--- Clearing Existing Data ---")
        cur.execute("TRUNCATE employees, projects, departments, users RESTART IDENTITY CASCADE")
        
        print("--- Seeding Departments ---")
        for org in ORGS:
            cur.execute("""
                INSERT INTO departments (name, location, budget) 
                VALUES (%s, %s, %s)
            """, (org.capitalize(), "Remote", random.randint(500000, 2000000)))
        
        # Get department IDs
        cur.execute("SELECT id, name FROM departments")
        dept_map = {name.lower(): id for id, name in cur.fetchall()}
        
        print("--- Seeding Production-Grade Multi-Tenant Data ---")
        
        employee_count = 0
        project_count = 0
        
        for tenant in TENANTS:
            print(f"  -> Seeding Tenant: {tenant}")
            tenant_orgs = random.sample(ORGS, k=random.randint(3, 5))
            
            for org in tenant_orgs:
                org_id = f"{tenant}_{org}"
                dept_id = dept_map[org]
                
                # Insert Employees & Production Identity Records
                num_employees = random.randint(15, 25)
                for i in range(num_employees):
                    f_name = random.choice(FIRST_NAMES)
                    l_name = random.choice(LAST_NAMES)
                    email = f"{f_name.lower()}.{l_name.lower()}.{tenant}.{org}.{i}@example.com"
                    pos = random.choice(POSITIONS)
                    sal = random.randint(50000, 150000)
                    uid = f"{tenant}_{org}_{i}"
                    h_date = "2023-01-01"
                    
                    # 1. Insert into Employee table
                    cur.execute("""
                        INSERT INTO employees (tenant_id, org_id, user_id, first_name, last_name, email, position, salary, department_id, hire_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (tenant, org_id, uid, f_name, l_name, email, pos, sal, dept_id, h_date))
                    
                    # 2. Insert into Production Identity Registry (users table)
                    access_levels = ["public", "internal"]
                    if pos in ["Lead", "Manager"]: access_levels.append("confidential")
                    if pos == "Scientist": access_levels.append("restricted")
                    
                    cur.execute("""
                        INSERT INTO users (user_id, tenant_id, org_id, sub_ids, roles, classification_access)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (uid, tenant, org_id, [org_id], [pos.lower()], access_levels))
                    
                    employee_count += 1
                
                # Insert Projects
                num_projects = random.randint(5, 10)
                for i in range(num_projects):
                    p_name = f"Project {org.capitalize()} {random.randint(100, 999)}"
                    status = random.choice(PROJECT_STATUS)
                    budget = random.randint(10000, 500000)
                    desc = f"A high-priority {org} initiative for {tenant} focusing on {random.choice(['AI', 'Cloud', 'Data', 'UX'])}."
                    uid_mgr = f"{tenant}_{org}_mgr_{i}"
                    s_date = "2024-01-15"
                    
                    cur.execute("""
                        INSERT INTO projects (tenant_id, org_id, user_id, name, status, budget, description, department_id, start_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (tenant, org_id, uid_mgr, p_name, status, budget, desc, dept_id, s_date))
                    project_count += 1
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"\nSUCCESS: Seeded {employee_count} users and {project_count} projects across 5 tenants.")
        
    except Exception as e:
        print(f"FAILED to seed database: {str(e)}")

if __name__ == "__main__":
    seed_database()

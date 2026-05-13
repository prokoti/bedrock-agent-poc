import boto3
import json
import re
import os
import psycopg2
from opensearch_service import get_opensearch_client
from dotenv import load_dotenv

load_dotenv()

# Configuration
REGION = os.getenv("AWS_REGION", "ap-south-1")
INDEX_NAME = os.getenv("OPENSEARCH_INDEX", "employee-knowledge")

# DB Configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

# Bedrock Client
bedrock = boto3.client(service_name="bedrock-runtime", region_name=REGION)

def classify_content(text):
    """
    Auto-classify logic for the Ingestion Pipeline.
    Levels: Public, Internal, Confidential, Restricted.
    """
    text_lower = text.lower()
    if any(word in text_lower for word in ["restricted", "top secret", "highly sensitive"]):
        return "restricted"
    if any(word in text_lower for word in ["salary", "budget", "bonus", "audit", "confidential"]):
        return "confidential"
    if any(word in text_lower for word in ["internal", "employee only", "proprietary"]):
        return "internal"
    return "public"

def apply_ai_eligibility_policy(content, metadata):
    """
    Step 6: Apply AI Eligibility Policy.
    Determines if the document can be used in certain GenAI scenarios.
    """
    # Example policy: Documents with PII redactions are 'enabled' for RAG
    if "[EMAIL_REDACTED]" in content or "[PHONE_REDACTED]" in content:
        return "enabled"
    # Restricted documents might be 'restricted' eligibility
    if metadata.get("classification") == "restricted":
        return "restricted"
    return "enabled"

def mask_pii(text):
    text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL_REDACTED]', text)
    text = re.sub(r'\+?\d{10,12}', '[PHONE_REDACTED]', text)
    return text

def generate_embeddings(text):
    body = json.dumps({"inputText": text})
    response = bedrock.invoke_model(
        body=body,
        modelId="amazon.titan-embed-text-v2:0",
        accept="application/json",
        contentType="application/json"
    )
    response_body = json.loads(response.get("body").read())
    return response_body.get("embedding")

def ingest_document(content, metadata, source="sql_db"):
    safe_content = mask_pii(content)
    classification = classify_content(content)
    
    # Enrichment
    metadata["classification"] = classification
    eligibility = apply_ai_eligibility_policy(safe_content, metadata)
    
    embedding = generate_embeddings(safe_content)
    
    client = get_opensearch_client()
    
    document = {
        "content": safe_content,
        "embedding": embedding,
        "metadata": {
            **metadata,
            "eligibility": eligibility,
            "source": source
        }
    }
    
    response = client.index(index=INDEX_NAME, body=document)
    return response

def ingest_from_sql():
    """Fetch data from PostgreSQL and ingest into OpenSearch."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("\n--- [POOLED Ingestion] Fetching Employees ---")
        cur.execute("""
            SELECT e.tenant_id, e.org_id, e.user_id, e.first_name, e.last_name, e.email, e.position, e.salary, d.name
            FROM employees e
            JOIN departments d ON e.department_id = d.id
        """)
        
        for row in cur.fetchall():
            tid, oid, uid, f_name, l_name, email, pos, sal, dept = row
            doc_text = f"Employee {f_name} {l_name} works as a {pos} in the {dept} department. Email: {email}. Salary: ${sal}."
            print(f"Ingesting Employee: {f_name} {l_name} [Tenant: {tid}, Org: {oid}]")
            
            metadata = {
                "tenant_id": tid,
                "org_id": oid,
                "user_id": uid,
                "data_type": "employee_record"
            }
            ingest_document(doc_text, metadata=metadata, source="employees_table")

        print("\n--- [POOLED Ingestion] Fetching Projects ---")
        cur.execute("SELECT tenant_id, org_id, user_id, name, status, budget, description FROM projects")
        for row in cur.fetchall():
            tid, oid, uid, p_name, status, budget, desc = row
            doc_text = f"Project '{p_name}' is currently {status} with a budget of ${budget}. Description: {desc}"
            print(f"Ingesting Project: {p_name} [Org: {oid}]")
            
            metadata = {
                "tenant_id": tid,
                "org_id": oid,
                "user_id": uid,
                "data_type": "project_record"
            }
            ingest_document(doc_text, metadata=metadata, source="projects_table")
            
        cur.close()
        conn.close()
        print("\n--- Ingestion Pipeline Complete ---")
        
    except Exception as e:
        print(f"Error during SQL ingestion: {str(e)}")

if __name__ == "__main__":
    ingest_from_sql()

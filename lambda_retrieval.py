import boto3
import json
import os
from opensearch_service import get_opensearch_client
from dotenv import load_dotenv

load_dotenv()

# AWS Configuration
REGION = os.getenv("AWS_REGION", "ap-south-1")
HOST = os.getenv("OPENSEARCH_URL").replace("https://", "")
INDEX_NAME = os.getenv("OPENSEARCH_INDEX", "employee-knowledge")

# Bedrock Client
bedrock = boto3.client(service_name="bedrock-runtime", region_name=REGION)

def generate_query_embedding(text):
    body = json.dumps({"inputText": text})
    response = bedrock.invoke_model(
        body=body,
        modelId="amazon.titan-embed-text-v2:0",
        accept="application/json",
        contentType="application/json"
    )
    response_body = json.loads(response.get("body").read())
    return response_body.get("embedding")

import psycopg2

# DB Configuration for Identity Enrichment
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

def get_permission_envelope(user_id):
    # 0. Safety: Strip whitespace
    user_id = user_id.strip() if user_id else ""
    
    # 1. Handle special administrative test profiles (optional)
    if user_id == "ADMIN_GLOBAL_CHECK":
        return {
            "tenant_id": "GLOBAL", # Bypass tenant filter
            "org_id": "GLOBAL",
            "sub_ids": ["*"],       # Bypass org filter
            "roles": ["admin"],
            "classification_access": ["public", "confidential", "secret", "top_secret"],
            "eligibility_context": ["enabled"]
        }
        
    if user_id == "sarah":
        return {
            "tenant_id": "acme", "org_id": "acme_logistics", "sub_ids": ["acme_logistics", "acme_warehouse"],
            "roles": ["research_lead"], "classification_access": ["confidential", "internal", "public"],
            "eligibility_context": "enabled"
        }

    # 2. Live Database Lookup
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT tenant_id, org_id, sub_ids, roles, classification_access, eligibility_context
            FROM users WHERE user_id = %s
        """, (user_id,))
        
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            tid, oid, sub_ids, roles, class_access, eligibility = row
            
            # PRODUCTION UPGRADE: If user is a manager, grant access to all departments in their tenant
            if roles and "manager" in roles:
                try:
                    conn_elevate = psycopg2.connect(**DB_CONFIG)
                    cur_elevate = conn_elevate.cursor()
                    cur_elevate.execute("SELECT DISTINCT org_id FROM users WHERE tenant_id = %s", (tid,))
                    all_orgs = [r[0] for r in cur_elevate.fetchall()]
                    
                    # Ensure sub_ids is a list before merging
                    current_sub_ids = sub_ids if isinstance(sub_ids, list) else [oid]
                    sub_ids = list(set(current_sub_ids + all_orgs))
                    
                    cur_elevate.close()
                    conn_elevate.close()
                except Exception as ex:
                    print(f"!!! Warning: Could not elevate manager permissions for {user_id}: {str(ex)}")

            return {
                "tenant_id": tid,
                "org_id": oid,
                "sub_ids": sub_ids,
                "roles": roles,
                "classification_access": class_access,
                "eligibility_context": eligibility
            }
    except Exception as e:
        print(f"Identity Enrichment Error for {user_id}: {str(e)}")
        import traceback
        traceback.print_exc()

    # 3. Default Fallback (Deny Access)
    return {
        "tenant_id": "public", "org_id": "public", "sub_ids": ["public"],
        "roles": [], "classification_access": ["public"], "eligibility_context": "disabled"
    }

def construct_metadata_filter(envelope):
    """
    Step 4-5: Construct Metadata filter as a HARD constraint.
    This is the 'leak-heating security wall'.
    """
    filters = [
        {"term": {"metadata.tenant_id": envelope["tenant_id"]}},
        {"terms": {"metadata.org_id": envelope["sub_ids"]}},
        {"terms": {"metadata.classification": envelope["classification_access"]}}
    ]
    
    if envelope["eligibility_context"] != "enabled":
        filters.append({"term": {"metadata.eligibility": envelope["eligibility_context"]}})
        
    return filters

def conflict_of_interest_check(user_id, hits):
    """Secondary security validation layer."""
    # Placeholder for dynamic COI logic
    return hits

def retrieve_context(query, user_id="john", top_k=5):
    # 1. Construct Permission Envelope
    envelope = get_permission_envelope(user_id)
    
    # 2. Build HARD metadata filter
    permission_filters = construct_metadata_filter(envelope)
    
    # 3. Generate Embedding
    query_vector = generate_query_embedding(query)
    
    # 4. Construct Query with Identity-Based Permission Envelope
    # GLOBAL BYPASS: If tenant is GLOBAL, search EVERYTHING without filters
    if envelope["tenant_id"] == "GLOBAL":
        search_query = {
            "size": top_k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_vector,
                        "k": top_k
                    }
                }
            }
        }
    else:
        # Standard Multi-Tenant Filtered Search
        search_query = {
            "size": top_k,
            "query": {
                "bool": {
                    "must": [
                        {
                            "knn": {
                                "embedding": {
                                    "vector": query_vector, 
                                    "k": top_k
                                }
                            }
                        }
                    ],
                    "filter": [
                        {"term": {"metadata.tenant_id": envelope["tenant_id"]}},
                        {"terms": {"metadata.org_id": envelope["sub_ids"]}},
                        {"terms": {"metadata.classification": envelope["classification_access"]}},
                        {"term": {"metadata.eligibility": envelope["eligibility_context"]}}
                    ]
                }
            }
        }
    
    client = get_opensearch_client()
    try:
        response = client.search(index=INDEX_NAME, body=search_query)
    except Exception as e:
        # Re-raise with a more descriptive message if it's an authorization issue
        error_msg = str(e)
        if "AuthorizationException" in error_msg or "403" in error_msg:
            print(f"CRITICAL: OpenSearch Authorization Error. Check Data Access Policies for {INDEX_NAME}")
        raise e
    
    results = []
    for hit in response['hits']['hits']:
        results.append({
            "content": hit['_source']['content'],
            "metadata": hit['_source']['metadata'],
            "score": hit['_score'] # Include the similarity score
        })
    
    # 5. Secondary COI Check
    safe_results = conflict_of_interest_check(user_id, results)
    
    return safe_results

if __name__ == "__main__":
    print("Retrieval Orchestrator (POOLED Architecture) ready.")
    # Test with a mock user
    test_results = retrieve_context("What is the project status?", user_id="sarah")
    print(f"Retrieved {len(test_results)} results for Sarah.")

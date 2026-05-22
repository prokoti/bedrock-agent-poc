import os
import json
from opensearch_service import get_opensearch_client
from dotenv import load_dotenv

load_dotenv()

INDEX_NAME = os.getenv("OPENSEARCH_INDEX", "employee-knowledge")

def inspect_all_data():
    client = get_opensearch_client()
    
    # Match all query
    query = {
        "size": 50, # Show top 50 docs
        "query": {
            "match_all": {}
        }
    }
    
    try:
        response = client.search(index=INDEX_NAME, body=query)
        hits = response['hits']['hits']
        
        print(f"\n--- Total Documents in OpenSearch: {response['hits']['total']['value']} ---\n")
        
        if not hits:
            print("No data found in the index.")
            return

        print(f"{'ID':<25} | {'Tenant':<10} | {'Org':<12} | {'User':<10} | {'Class':<10} | {'Content Summary'}")
        print("-" * 120)

        for hit in hits:
            doc_id = hit['_id']
            source = hit['_source']
            meta = source.get('metadata', {})
            content = source.get('content', '')[:50].replace('\n', ' ') + "..."
            
            classification = meta.get('classification', 'N/A')
            tenant = meta.get('tenant_id', 'N/A')
            org = meta.get('org_id', 'N/A')
            user = meta.get('user_id', 'N/A')
            
            print(f"{doc_id:<25} | {tenant:<10} | {org:<12} | {user:<10} | {classification:<10} | {content}"
        print("\n" + "="*100 + "\n")
            
    except Exception as e:
        print(f"Error inspecting data: {str(e)}")

def search_johnson():
    client = get_opensearch_client()
    query = {
        "query": {
            "match": {
                "content": "Uber"
            }
        }
    }
    response = client.search(index=INDEX_NAME, body=query)
    print(f"\n--- OpenSearch results for 'Uber' ({len(response['hits']['hits'])} found) ---")
    for hit in response['hits']['hits']:
        print(f"ID: {hit['_id']}")
        print(f"Content: {hit['_source']['content']}")
        print(f"Metadata: {hit['_source']['metadata']}")
        print("-" * 40)
  
if __name__ == "__main__":
    search_johnson()
    
import os
import json
from opensearch_service import get_opensearch_client
from dotenv import load_dotenv

load_dotenv()

INDEX_NAME = os.getenv("OPENSEARCH_INDEX", "employee-knowledge")

def create_index():
    client = get_opensearch_client()
    
    # Define index settings and mappings for k-NN
    # Note: For Serverless (aoss), we use specialized mappings
    index_body = {
        "settings": {
            "index.knn": True
        },
        "mappings": {
            "properties": {
                "embedding": {
                    "type": "knn_vector",
                    "dimension": 1024, # Titan Embeddings v2 dimension
                    "method": {
                        "name": "hnsw",
                        "engine": "nmslib",
                        "space_type": "l2"
                    }
                },
                "content": {"type": "text"},
                "metadata": {
                    "properties": {
                        "tenant_id": {"type": "keyword"},
                        "org_id": {"type": "keyword"},
                        "user_id": {"type": "keyword"},
                        "classification": {"type": "keyword"},
                        "eligibility": {"type": "keyword"},
                        "source": {"type": "keyword"}
                    }
                }
            }
        }
    }

    if not client.indices.exists(index=INDEX_NAME):
        print(f"Creating index: {INDEX_NAME}...")
        response = client.indices.create(index=INDEX_NAME, body=index_body)
        print(f"Response: {response}")
    else:
        print(f"Index {INDEX_NAME} already exists.")

if __name__ == "__main__":
    create_index()

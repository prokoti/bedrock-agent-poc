import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def get_collection_details():
    region = os.getenv("AWS_REGION", "ap-south-1")
    url = os.getenv("OPENSEARCH_URL", "")
    # Extract ID from URL
    if not url:
        print("No OPENSEARCH_URL in .env")
        return
        
    collection_id = url.split("//")[1].split(".")[0]
    print(f"Collection ID: {collection_id}")
    
    client = boto3.client("opensearchserverless", region_name=region)
    try:
        response = client.batch_get_collection(ids=[collection_id])
        details = response.get("collectionDetails", [])
        if details:
            c = details[0]
            print(f"Name: {c['name']}")
            print(f"ARN: {c['arn']}")
            print(f"Status: {c['status']}")
            print(f"Type: {c['type']}")
        else:
            print("Collection not found.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    get_collection_details()

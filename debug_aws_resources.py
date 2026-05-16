import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def debug_resources():
    regions = ["ap-south-1", "us-east-1", "us-west-2"]
    
    print("--- DEBUGGING AWS RESOURCES ---")
    
    # 1. Check OpenSearch Serverless Collections
    print("\n[OpenSearch Serverless Collections]")
    for region in regions:
        try:
            client = boto3.client("opensearchserverless", region_name=region)
            response = client.list_collections()
            collections = response.get("collectionSummaries", [])
            if collections:
                print(f"✅ Found {len(collections)} collection(s) in {region}:")
                for c in collections:
                    print(f"   - Name: {c['name']}, ID: {c['id']}, Status: {c['status']}")
            else:
                print(f"   (No collections in {region})")
        except Exception as e:
            print(f"   ❌ Error in {region}: {str(e)}")

    # 2. Check Bedrock Guardrails
    print("\n[Bedrock Guardrails]")
    for region in regions:
        try:
            client = boto3.client("bedrock", region_name=region)
            response = client.list_guardrails()
            guardrails = response.get("guardrailSummaries", [])
            if guardrails:
                print(f"✅ Found {len(guardrails)} guardrail(s) in {region}:")
                for g in guardrails:
                    print(f"   - Name: {g['name']}, ID: {g['id']}, Status: {g['status']}")
            else:
                print(f"   (No guardrails in {region})")
        except Exception as e:
            print(f"   ❌ Error in {region}: {str(e)}")

if __name__ == "__main__":
    debug_resources()

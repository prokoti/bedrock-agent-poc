import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def inspect_guardrail():
    region = os.getenv("AWS_REGION", "ap-south-1")
    guardrail_id = os.getenv("GUARDRAIL_ID")
    
    guardrail_version = os.getenv("GUARDRAIL_VERSION", "DRAFT")
    
    if not guardrail_id:
        print("Error: No GUARDRAIL_ID found in .env")
        return

    print(f"--- Inspecting Guardrail Config: {guardrail_id} (Version: {guardrail_version}) ---")
    client = boto3.client("bedrock", region_name=region)
    
    try:
        response = client.get_guardrail(
            guardrailIdentifier=guardrail_id,
            guardrailVersion=guardrail_version
        )
        
        print(f"Name: {response.get('name')}")
        print(f"Status: {response.get('status')}")
        
        # Check Content Filters
        content_filters = response.get("contentPolicy", {}).get("filters", [])
        print("\n[Content Filters]")
        if not content_filters:
            print("WARNING: No content filters are defined! (It won't block violence/hate)")
        for f in content_filters:
            print(f"- {f['type']}: Input={f['inputStrength']}, Output={f['outputStrength']}")

        # Check Sensitive Information Policy
        pii_entities = response.get("sensitiveInformationPolicy", {}).get("piiEntities", [])
        print("\n[PII Filters]")
        print(f"Count: {len(pii_entities)}")

    except Exception as e:
        print(f"Error: Could not inspect guardrail. {str(e)}")

if __name__ == "__main__":
    inspect_guardrail()


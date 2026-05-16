import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def scan_for_guardrails():
    # Test common Bedrock regions
    regions = ["ap-south-1", "us-east-1", "us-west-2"]
    
    print("--- Scanning for Bedrock Guardrails ---")
    
    found_any = False
    for region in regions:
        print(f"Checking {region}...")
        try:
            client = boto3.client("bedrock", region_name=region)
            response = client.list_guardrails()
            
            summaries = response.get("guardrailSummaries", [])
            if summaries:
                found_any = True
                print(f"✅ Found {len(summaries)} Guardrail(s) in {region}:")
                for g in summaries:
                    print(f"   - Name: {g['name']}")
                    print(f"   - ID: {g['id']}")
                    print(f"   - Status: {g['status']}")
            else:
                print(f"   (No guardrails found in {region})")
                
        except Exception as e:
            print(f"   ❌ Could not check {region}: {str(e)}")

    if not found_any:
        print("\n❌ Summary: No Guardrails found in any tested region. Please ensure you have created one in the AWS Console.")

if __name__ == "__main__":
    scan_for_guardrails()

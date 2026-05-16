import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def scan_all_regions():
    # Full list of Bedrock regions as of current knowledge
    regions = [
        "us-east-1", "us-west-2", "ap-south-1", "ap-southeast-1", 
        "ap-southeast-2", "ap-northeast-1", "eu-central-1", "eu-west-1",
        "ca-central-1", "sa-east-1"
    ]
    
    print("--- Comprehensive Guardrail Scan ---")
    
    found_any = False
    for region in regions:
        print(f"Checking {region}...", end=" ", flush=True)
        try:
            client = boto3.client("bedrock", region_name=region)
            response = client.list_guardrails()
            summaries = response.get("guardrailSummaries", [])
            if summaries:
                found_any = True
                print(f"✅ FOUND {len(summaries)}")
                for g in summaries:
                    print(f"   - Name: {g['name']}, ID: {g['id']}, Region: {region}")
            else:
                print("none")
        except Exception as e:
            print(f"error ({str(e).split(':')[0]})")

    if not found_any:
        print("\n❌ No Guardrails found in any region. Are you sure you're using the same AWS account as yesterday?")

if __name__ == "__main__":
    scan_all_regions()

import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

def verify_guardrail():
    region = os.getenv("AWS_REGION", "ap-south-1")
    guardrail_id = os.getenv("GUARDRAIL_ID")
    guardrail_version = os.getenv("GUARDRAIL_VERSION", "DRAFT")
    
    if not guardrail_id:
        print("❌ Error: No GUARDRAIL_ID found in .env")
        return

    print(f"--- Testing Bedrock Guardrail: {guardrail_id} ---")
    bedrock_runtime = boto3.client("bedrock-runtime", region_name=region)
    
    # We will send a prompt that should be safe, just to test connectivity
    test_body = {
        "prompt": "Hello, tell me about company culture.",
        "max_gen_len": 100
    }
    
    try:
        response = bedrock_runtime.invoke_model(
            modelId="meta.llama3-8b-instruct-v1:0",
            body=json.dumps(test_body),
            guardrailIdentifier=guardrail_id,
            guardrailVersion=guardrail_version,
            trace="ENABLED"
        )
        
        print("Connectivity: SUCCESS (The Guardrail is active and reachable)")
        
        response_body = json.loads(response.get("body").read())
        action = response.get("action")
        
        if action == "GUARDRAIL_INTERVENED":
            print("Safety Filter: ACTIVE (A policy was triggered)")
        else:
            print("Safety Filter: PASSED (Prompt was deemed safe)")
            
    except Exception as e:
        print(f"Error: Guardrail setup failed. Details: {str(e)}")
        if "AccessDeniedException" in str(e):
            print("Recommendation: Your IAM role needs 'bedrock:ApplyGuardrail' permission.")

if __name__ == "__main__":
    verify_guardrail()

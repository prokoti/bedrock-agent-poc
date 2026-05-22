import os
import json
import boto3
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage

# Local import
from lambda_retrieval import retrieve_context

load_dotenv()

REGION = os.getenv("AWS_REGION", "ap-south-1")
GUARDRAIL_ID = os.getenv("GUARDRAIL_ID")
GUARDRAIL_VERSION = os.getenv("GUARDRAIL_VERSION", "DRAFT")

bedrock_runtime = boto3.client(service_name="bedrock-runtime", region_name=REGION)

def generate_response(user_query, user_id="john", agent_type="COREAIAGENT"):
    """
    Main Orchestrator for Multi-Tenant RAG.
    1. Identity Enrichment (Tenant Check)
    2. Context Retrieval (Multi-Level)
    3. Security Wall Enforcement (Access vs Domain)
    4. Guardrail-Protected Inference
    """
    print(f"--- Processing Query for {user_id} ---")
    
    # --- PROACTIVE SECURITY: Input Guardrail Check ---
    try:
        guardrail_response = bedrock_runtime.apply_guardrail(
            guardrailIdentifier=GUARDRAIL_ID,
            guardrailVersion=GUARDRAIL_VERSION,
            source="INPUT",
            content=[{"text": {"text": user_query}}]
        )
        
        if guardrail_response.get("action") == "GUARDRAIL_INTERVENED":
            print(f"[Input Guardrail] BLOCKED toxic query from {user_id}")
            return {
                "result": "[Security Block] Your request contains content that violates our safety policies and has been blocked.",
                "agent": "INPUT_GUARDRAIL",
                "version": "v2.2",
                "citations": []
            }
    except Exception as g_err:
        print(f"Warning: Guardrail check failed: {str(g_err)}")
        # We continue if guardrail check fails technically, but log it.
    
    # 1 & 2. Perform Dual-Retrieval (Global check + Secure Filtered)
    try:
        global_results = retrieve_context(user_query, user_id="ADMIN_GLOBAL_CHECK")
        secure_results = retrieve_context(user_query, user_id=user_id)
    except Exception as ret_err:
        print(f"ERROR: Retrieval Error: {str(ret_err)}")
        if "AuthorizationException" in str(ret_err) or "403" in str(ret_err):
            return {
                "result": "System Error: The security wall is currently unable to verify data permissions. Please contact your administrator to check OpenSearch Data Access Policies.",
                "agent": "ORCHESTRATOR",
                "version": "v2.2"
            }
        return {"result": f"System Error during retrieval: {str(ret_err)}", "version": "v2.2"}

    # Logic Implementation with Confidence Threshold (0.25 score)
    global_top_score = max([hit.get('score', 0) for hit in global_results], default=0)
    secure_top_score = max([hit.get('score', 0) for hit in secure_results], default=0)
    
    print(f"DEBUG SECURITY: Global Top Score={global_top_score:.4f} | Secure Top Score={secure_top_score:.4f}")

    has_global_data = global_top_score > 0.25
    has_secure_data = secure_top_score > 0.25
    
    if not has_global_data:
        return {
            "result": "This question does not belong to your company details",
            "agent": "DOMAIN_WALL",
            "version": "v2.2",
            "citations": []
        }
        
    if has_global_data and not has_secure_data:
        return {
            "result": "You dont have the access to these datas",
            "agent": "SECURITY_WALL",
            "version": "v2.2",
            "citations": []
        }

    # 4. Construct Prompt with authorized results only
    context_text = "\n".join([f"[Source {i+1}]: {r['content']}" for i, r in enumerate(secure_results)])
    
    system_prompt = f"""
    You are a secure corporate assistant. Use the following authorized context to answer.
    If the answer is not in the context, say you don't know.
    Always cite sources like [Source 1].
    
    CONTEXT:
    {context_text}
    """

    messages = [
        {"role": "user", "content": user_query}
    ]

    # 5. Invoke Model with Guardrails (Using Cross-Region Inference ID)
    try:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": messages,
            "temperature": 0
        })

        # Fix: Use the APAC Inference Profile ID (required for on-demand throughput in ap-south-1)
        model_to_use = "apac.anthropic.claude-3-5-sonnet-20240620-v1:0"
        
        response = bedrock_runtime.invoke_model(
            modelId=model_to_use, 
            body=body,
            guardrailIdentifier=GUARDRAIL_ID,
            guardrailVersion=GUARDRAIL_VERSION,
            trace="ENABLED"
        )

        response_body = json.loads(response.get("body").read())
        
        # Check for Guardrail Intervention in Amazon Bedrock Trace
        amazon_trace = response.get('amazon-bedrock-trace', {})
        guardrail_trace = amazon_trace.get('guardrail', {})
        
        # Debugging: Print trace details to terminal
        if guardrail_trace:
            action = guardrail_trace.get('action')
            if action == 'INTERVENED':
                print(f"[Bedrock Guardrail] INTERVENED for {user_id}")
                # Log specific policy violation if available
                outputs = guardrail_trace.get('outputs', [])
                for out in outputs:
                    print(f"   Violation: {out.get('text')}")

        generation = response_body.get("content", [{"text": "Error: No response"}])[0].get("text")
        citations = [r.get('metadata') for r in secure_results]

        return {
            "result": generation,
            "agent": "LLM_GEN",
            "version": "v2.2",
            "citations": citations
        }

    except Exception as e:
        error_msg = str(e)
        if "Guardrail" in error_msg or "sensitive" in error_msg.lower():
            return {
                "result": "[Security Block] Your request or the AI response violated our safety policy and was blocked.",
                "agent": "GUARDRAIL_INTERVENTION",
                "version": "v2.2",
                "citations": []
            }
        print(f"Error invoking model: {error_msg}")
        return {"result": f"System Error: {error_msg}", "version": "v2.2"}

if __name__ == "__main__":
    # Test
    res = generate_response("What is the revenue of Glovex?", user_id="acme_logistics_11", agent_type="COREAIAGENT")
    print(json.dumps(res, indent=2))

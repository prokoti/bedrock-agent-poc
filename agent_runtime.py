import os
import json
import boto3
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Local import
from lambda_retrieval import retrieve_context

load_dotenv()

REGION = os.getenv("AWS_REGION", "ap-south-1")
# Agent Catalog: Each tenant has TWO agents (logical configs on shared AgentCore runtime)
AGENT_CATALOG = {
    "ONBOARDINGAGENT": {
        "description": "Handles functional setup phase",
        "tools": ["mapping-generator", "ui-coverage-analyzer"],
        "kb_scope": "onboarding_artifacts"
    },
    "COREAIAGENT": {
        "description": "General purpose agent for daily operations",
        "tools": ["release-tracker", "action-outcome", "decision-historian"],
        "kb_scope": "all_tenant_content"
    }
}

app = BedrockAgentCoreApp()
llm = ChatBedrock(model_id="meta.llama3-8b-instruct-v1:0", region_name=REGION)

def apply_guardrails(text, stage="input"):
    """
    Step 8-10: Bedrock AgentCore + Guardrails.
    Prevents prompt injection, PII, and denied topics.
    """
    if stage == "input":
        # Denied Topics Simulation
        denied_topics = ["competitor comparison", "illegal activity"]
        if any(topic in text.lower() for topic in denied_topics):
            return False, "Guardrail Alert: Denied topic detected."
            
        # Prompt Injection Simulation
        if "ignore previous instructions" in text.lower() or "dan mode" in text.lower():
            return False, "Guardrail Alert: Malicious prompt detected."
            
    return True, text

def generate_response(user_query: str, user_id: str = "john", agent_type: str = "COREAIAGENT"):
    # 1. Identify Agent from Catalog
    agent_config = AGENT_CATALOG.get(agent_type, AGENT_CATALOG["COREAIAGENT"])
    
    # 2. Input Guardrails
    is_safe, message = apply_guardrails(user_query, stage="input")
    if not is_safe: return {"result": message}

    # 3. Secure Retrieval with Identity Envelope
    context_results = retrieve_context(user_query, user_id=user_id)
    if not context_results: return {"result": "You dont have the access to these datas"}

    # 4. Construct Prompt with Citations Logic
    context_text = "\n".join([f"[Source {i+1}]: {r['content']}" for i, r in enumerate(context_results)])
    
    system_prompt = (
        f"You are the {agent_type}. {agent_config['description']}.\n"
        "Answer the user's question based ONLY on the provided context.\n"
        "STRICT RULE: Every sentence must track to source chunks using [Source X] format.\n"
        f"CONTEXT:\n{context_text}"
    )
    
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_query)]
    
    # 5. Model Invocation
    response = llm.invoke(messages)
    
    # 6. Output Guardrails (Optional)
    # is_output_safe, output_message = apply_guardrails(response.content, stage="output")
    
    return {
        "result": response.content,
        "agent": agent_type,
        "citations": [r['metadata'] for r in context_results]
    }

@app.entrypoint
def agent_invocation(payload, context):
    user_prompt = payload.get("prompt", "")
    user_id = payload.get("user_id", "john")
    agent_type = payload.get("agent_type", "COREAIAGENT")
    return generate_response(user_prompt, user_id=user_id, agent_type=agent_type)

if __name__ == "__main__":
    print(f"Bedrock AgentCore Runtime active with {len(AGENT_CATALOG)} agents in catalog.")
    app.run()

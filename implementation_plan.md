# Implementation Plan: Prokoti GenAI - POOLED Architecture Alignment

This plan updates the existing RAG and Agent codebase to strictly follow the **Prokoti GenAI POOLED Architecture**, focusing on identity-driven isolation, metadata-filter security walls, and an enhanced ingestion pipeline.

## User Review Required

> [!IMPORTANT]
> **Metadata Schema Changes**: This update introduces new metadata fields (`sub_ids`, `classification` with 4 levels, `eligibility`). Existing data in OpenSearch might need re-indexing to be fully compatible with the new filters.
> **Mock Identity Service**: I will implement a robust mock for the "Identity Enrichment Chain" (Step 1-3) since we don't have a live Cognito/Auth Service connection.

## Proposed Changes

### [Component 1] Retrieval Orchestrator (Lambda)
Update the retrieval logic to enforce the "Leak-Heating Security Wall" using a hard metadata filter constraint.

#### [MODIFY] [lambda_retrieval.py](file:///c:/Users/YOGA/Desktop/prokoti_agent_bedrock/lambda_retrieval.py)
- **Implement `get_permission_envelope(user_id)`**: Fetch full identity details: `tenant_id`, `org_id`, `sub_ids`, `roles`, `classification_access`, `scenario_id`, `eligibility_context`.
- **Implement `construct_metadata_filter(envelope)`**: Build the OpenSearch `bool` filter based on the envelope.
- **Add `conflict_of_interest_check(user_id, document_metadata)`**: A secondary validation layer.

---

### [Component 2] Ingestion Pipeline (Data Enrichment)
Upgrade the ingestion logic to support granular classification and eligibility policies.

#### [MODIFY] [lambda_ingestion.py](file:///c:/Users/YOGA/Desktop/prokoti_agent_bedrock/lambda_ingestion.py)
- **Enhanced `classify_content(text)`**: Support `Public`, `Internal`, `Confidential`, `Restricted`.
- **New `apply_ai_eligibility_policy(content, metadata)`**: Tags documents with eligibility markers (e.g., `eligibility: enabled`).
- **Update Metadata Schema**: Include `sub_ids` and `account_context`.

---

### [Component 3] AgentCore Runtime & Catalog
Refactor the agent runtime to simulate the "Agent Catalog" and implement strict guardrails.

#### [MODIFY] [agent_runtime.py](file:///c:/Users/YOGA/Desktop/prokoti_agent_bedrock/agent_runtime.py)
- **Define Agent Catalog**: Separate configs for `ONBOARDINGAGENT` and `COREAIAGENT`.
- **Strengthen Guardrails**: Implement Bedrock Guardrails simulation for PII and Prompt Injection.
- **Implement Citations Logic**: Ensure responses attribute facts to source chunks.

---

### [Component 4] OpenSearch Schema (Setup)
#### [MODIFY] [opensearch_setup.py](file:///c:/Users/YOGA/Desktop/prokoti_agent_bedrock/opensearch_setup.py)
- Update the index mapping to ensure metadata fields are searchable and correctly typed.

## Verification Plan

### Automated Tests
- **Identity Isolation Test**: Run `lambda_retrieval.py` for different users (Sarah, John, Priya from diagram) and verify they ONLY see authorized subsets.
- **Ingestion Validation**: Run `lambda_ingestion.py` on a sample dataset containing restricted info and verify tags.
- **Agent Flow Test**: Use `test_agent.py` to trigger both `ONBOARDINGAGENT` and `COREAIAGENT` flows.

### Manual Verification
- Review the `search_query` JSON generated in `lambda_retrieval.py` to ensure the `filter` block is correctly constructed as a "Hard Constraint".

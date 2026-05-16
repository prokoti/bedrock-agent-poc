from lambda_retrieval import retrieve_context
import json

def debug_glovex():
    print("--- Searching for 'glovex' in Global Index ---")
    results = retrieve_context("glovex", user_id="ADMIN_GLOBAL_CHECK")
    
    if not results:
        print("No results found for 'glovex' anywhere.")
        return

    print(f"Found {len(results)} matches.")
    for i, r in enumerate(results):
        score = r.get('score', 0)
        meta = r.get('metadata', {})
        tenant = meta.get('tenant_id')
        org = meta.get('org_id')
        print(f"[{i+1}] Score: {score:.4f} | Tenant: {tenant} | Org: {org}")
        print(f"    Snippet: {r.get('content')[:100]}...")
        print("-" * 40)

if __name__ == "__main__":
    debug_glovex()

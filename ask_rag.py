from agent_runtime import generate_response

def start_chat():
    print("\n" + "="*50)
    print("PROKOTI RAG AGENT - INTERACTIVE SESSION")
    print("="*50)
    print("Type 'exit' to end the session.\n")

    while True:
        print("-" * 30)
        user_id = input("Enter User ID (e.g., acme_research_0, umbrella_research_5, sarah): ").strip()
        if user_id.lower() == 'exit':
            break
            
        query = input(f"Question for {user_id}: ").strip()
        if query.lower() == 'exit':
            break
            
        if not query or not user_id:
            print("Please provide both User ID and a Question.")
            continue

        print("\nSearching knowledge base and generating response...")
        try:
            response = generate_response(query, user_id=user_id)
            print(f"\nAI RESPONSE:\n{response['result']}\n")
        except Exception as e:
            print(f"\nERROR: {str(e)}\n")

if __name__ == "__main__":
    start_chat()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from agent_runtime import generate_response

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    messages: Optional[List[Dict[str, Any]]] = None
    user_id: Optional[str] = "sarah"  # Default user for testing identity

@app.post("/api/chat")
def chat(request: ChatRequest):
    print(f"Received request from frontend: {request.query} (User: {request.user_id})")
    
    # Call the existing orchestrator logic
    response = generate_response(request.query, user_id=request.user_id)
    
    # Map to frontend expected format
    return {
        "answer": response.get("result", "An error occurred."),
        "sources": response.get("citations", []),
        "relevant": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

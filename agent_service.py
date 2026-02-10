from fastapi import FastAPI, Request
import sys
from google import genai

app = FastAPI()

# Identity assigned at startup
AGENT_NAME = sys.argv[1]
PORT = sys.argv[2]
API_KEY = sys.argv[3]

@app.get("/.well-known/agent-card.json")
async def get_card():
    return {
        "version": "1.0",
        "name": f"EARTH-{AGENT_NAME}-Agent",
        "url": f"http://localhost:{PORT}",
        "endpoints": {"a2a_v1": f"http://localhost:{PORT}/a2a/v1"},
        "capabilities": {"geomythology-synthesis": True, "tasks-send": True}
    }

@app.post("/a2a/v1")
async def handle_a2a_request(request: Request):
    payload = await request.json()
    
    # Official A2A JSON-RPC 2.0 Method
    if payload.get("method") == "tasks/send":
        user_query = payload['params']['message']['parts'][0]['text']
        inventory = payload['params'].get('context', '')

        client = genai.Client(api_key=API_KEY)
        instruction = f"Role: {AGENT_NAME} Agent for E.A.R.T.H. Query: {user_query}. Context: {inventory}."
        
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=instruction
        )
        
        # A2A Spec: Return Artifact result
        return {
            "jsonrpc": "2.0",
            "id": payload.get("id"),
            "result": {
                "status": "completed",
                "output": [{"type": "text", "text": response.text, "name": f"{AGENT_NAME}_Report"}]
            }
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(PORT))
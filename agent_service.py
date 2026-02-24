from fastapi import FastAPI, Request
import sys
import json
from google import genai

app = FastAPI()

# Identity
AGENT_NAME = sys.argv[1]
PORT = sys.argv[2]
API_KEY = sys.argv[3]

# A2A DISCOVERY: Standardized Agent Card
@app.get("/.well-known/agent-card.json")
async def get_card():
    card = {
        "version": "1.0",
        "name": f"EARTH-{AGENT_NAME.replace(' ', '-')}-Agent",
        "url": f"http://localhost:{PORT}",
        "endpoints": {"a2a_v1": f"http://localhost:{PORT}/a2a/v1"},
        "capabilities": {"geomythology-synthesis": True, "tasks-send": True}
    }
    print(f"\n[A2A DISCOVERY HANDSHAKE]: Broadcasting Protocol Card...")
    return card

# A2A INTERACTION: JSON-RPC 2.0 Method Handling
@app.post("/a2a/v1")
async def handle_a2a_request(request: Request):
    payload = await request.json()
    
    # Telemetry
    print(f"\n[INCOMING A2A MESSAGE] --- ID: {payload.get('id')}")
    print(f"Method: {payload.get('method')}")

    if payload.get("method") == "tasks/send":
        user_query = payload['params']['message']['parts'][0]['text']
        truth_data = payload['params'].get('context', 'NO DATA')

        client = genai.Client(api_key=API_KEY)
        
        # DISCIPLINARY LOGIC
        if AGENT_NAME == "Art Critic":
            role_prompt = "You are the Senior Curatorial Lead and Art Critic for the E.A.R.T.H. Gallery. MISSION: Perform a formalist analysis of the Architect's shading and pareidolia. Compare to high-art history (Chiaroscuro, Michelangelo, Bernini)."
        else:
            role_prompt = f"You are the Senior {AGENT_NAME} Fellow. MISSION: Research the actual history, DNA, and science of the coordinates provided. DO NOT search for geoglyphs; search for local lore/facts."

        instruction = f"{role_prompt}\nSubject: {user_query}\nCoordinates Ingested: {truth_data}\nProvide a massive, long-form academic report."
        
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=instruction,
            config={"max_output_tokens": 8192, "temperature": 0.3}
        )
        
        print(f"[A2A ARTIFACT]: Generated {len(response.text)} bytes of research data.")
        
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
    print(f"--- {AGENT_NAME} AGENT LISTENING ON PORT {PORT} ---")
    uvicorn.run(app, host="127.0.0.1", port=int(PORT), log_level="error")

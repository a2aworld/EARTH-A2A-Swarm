from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer
import sys, json, os, jwt
from google import genai
from dotenv import load_dotenv

# Load Security Vault
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
SECRET_KEY = os.getenv("A2A_SECRET_KEY")

app = FastAPI()
security = HTTPBearer()

AGENT_NAME = sys.argv[1].replace(' ', '_')
PORT = sys.argv[2]

# Load Identity
with open(f"D:/A2A_WORLD/agent_cards/{AGENT_NAME}_card.json", 'r') as f:
    AGENT_CARD = json.load(f)

# JWT Authentication Middleware
def verify_token(credentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        if payload.get("iss") != "earth-orchestrator": raise Exception
    except:
        raise HTTPException(status_code=401, detail="A2A Protocol: Unauthorized Handshake")

@app.get("/.well-known/agent-card.json")
async def get_card():
    return AGENT_CARD

# Secure, Compliant Task Endpoint
@app.post("/a2a/v1", dependencies=[Depends(verify_token)])
async def handle_a2a_request(request: Request):
    payload = await request.json()
    
    # Strict JSON-RPC 2.0 Validation
    if payload.get("jsonrpc") != "2.0" or payload.get("method") != "tasks/send":
        raise HTTPException(status_code=400, detail="Invalid A2A JSON-RPC format")
        
    task_id = payload.get("id", "unknown_task")
    user_query = payload['params']['message']['parts'][0]['text']
    truth_data = payload['params'].get('context', '')

    client = genai.Client(api_key=API_KEY)
    instruction = f"ROLE: {AGENT_NAME} Specialist. DATA: {truth_data}. QUERY: {user_query}. Provide a rigorous, forensic academic analysis. Do not morph geography."
    
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=instruction,
        config={"max_output_tokens": 8192, "temperature": 0.2}
    )
    
    # Official A2A Artifact Response
    return {
        "jsonrpc": "2.0",
        "id": task_id,
        "result": {
            "status": "completed",
            "output":[{
                "type": "artifact",
                "name": f"{AGENT_NAME}_Dossier",
                "parts":[{"type": "text", "text": response.text}]
            }]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(PORT), log_level="warning")

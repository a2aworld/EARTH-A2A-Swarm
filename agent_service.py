from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer
import sys, json, os, jwt, asyncio, httpx, time
from google import genai
from dotenv import load_dotenv

# ADK 2.0 Imports
from google.adk import Agent
from google.adk.tools import FunctionTool
from google.adk.runners import InMemoryRunner

# Registry for Peer Discovery
from agent_registry import AGENT_REGISTRY

# Load Security Configuration
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
SECRET_KEY = os.getenv("A2A_SECRET_KEY")

app = FastAPI()
security = HTTPBearer()

AGENT_NAME = sys.argv[1].replace(' ', '_')
PORT = sys.argv[2]

# Load Identity
try:
    with open(f"./agent_cards/{AGENT_NAME}_card.json", 'r') as f:
        AGENT_CARD = json.load(f)
except FileNotFoundError:
    AGENT_CARD = {"name": f"EARTH-{AGENT_NAME}-Agent"}

# JWT Authentication Middleware
def verify_token(credentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        if payload.get("iss") not in ["earth-orchestrator", "earth-agent"]: raise Exception
    except:
        raise HTTPException(status_code=401, detail="A2A Protocol: Unauthorized Handshake")

def generate_agent_token():
    return jwt.encode({"iss": "earth-agent", "sub": AGENT_NAME, "exp": time.time() + 300}, SECRET_KEY, algorithm="HS256")

# --- ADK 2.0 Specialized Functions ---

async def analyze_geospatial_data(context_data: str, research_query: str) -> str:
    """
    Analyzes geospatial and geomythological data points to extract academic insights.
    """
    client = genai.Client(api_key=API_KEY)
    instruction = f"ROLE: {AGENT_NAME} Specialist. DATA: {context_data}. QUERY: {research_query}. Provide a rigorous, forensic academic analysis."

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=instruction,
        config={"max_output_tokens": 8192, "temperature": 0.2}
    )
    return response.text

async def consult_peer_specialist(specialty: str, query: str, context: str) -> str:
    """
    Consults a peer specialist in the mesh network for additional insights.
    """
    if specialty not in AGENT_REGISTRY:
        return f"Error: Specialty '{specialty}' not found in network registry."

    peer_port = AGENT_REGISTRY[specialty]['port']
    token = generate_agent_token()
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "jsonrpc": "2.0", "method": "tasks/send", "id": f"peer_{int(time.time())}",
        "params": {"message": {"parts":[{"text": query}]}, "context": context}
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"http://localhost:{peer_port}/a2a/v1", json=payload, headers=headers, timeout=60.0)
            return response.json()['result']['output'][0]['parts'][0]['text']
        except Exception as e:
            return f"Failed to consult {specialty}: {str(e)}"

# Define the ADK Agent
adk_agent = Agent(
    name=AGENT_NAME,
    instruction=f"You are a specialized {AGENT_NAME} researcher. Use consult_peer_specialist when you need interdisciplinary verification.",
    tools=[
        FunctionTool(analyze_geospatial_data),
        FunctionTool(consult_peer_specialist)
    ]
)

@app.get("/.well-known/agent-card.json")
async def get_card():
    return AGENT_CARD

@app.post("/a2a/v1", dependencies=[Depends(verify_token)])
async def handle_a2a_request(request: Request):
    payload = await request.json()
    if payload.get("jsonrpc") != "2.0" or payload.get("method") != "tasks/send":
        raise HTTPException(status_code=400, detail="Invalid A2A JSON-RPC format")

    user_query = payload['params']['message']['parts'][0]['text']
    truth_data = payload['params'].get('context', '')

    # Use ADK Runner to execute agent
    runner = InMemoryRunner(agent=adk_agent)
    final_analysis = ""
    async for event in runner.run_async(
        user_id="earth_system",
        session_id=f"agent_session_{int(time.time())}",
        new_message={"parts": [{"text": f"Analyze this: {user_query}. Context: {truth_data}"}]}
    ):
        if event.output:
            final_analysis = event.output

    # Fallback to direct tool call if runner output is empty in simulation
    if not final_analysis:
        final_analysis = await analyze_geospatial_data(context_data=truth_data, research_query=user_query)

    return {
        "jsonrpc": "2.0",
        "id": payload.get("id"),
        "result": {
            "status": "completed",
            "output":[{
                "type": "artifact",
                "name": f"{AGENT_NAME}_Dossier",
                "parts":[{"type": "text", "text": final_analysis}]
            }]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(PORT), log_level="warning")

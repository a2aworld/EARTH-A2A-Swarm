import bootstrap # Sovereign Framework Injection
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer
import sys, json, os, jwt, asyncio, httpx, time
from google import genai
from google.genai import types as genai_types
from dotenv import load_dotenv

# ADK 2.0 Robust Imports
try:
    from google.adk import Agent
    from google.adk.tools import FunctionTool
    from google.adk.runners import InMemoryRunner
except ImportError:
    Agent = FunctionTool = InMemoryRunner = None

# Registry for Peer Discovery
try:
    from agent_registry import AGENT_REGISTRY
except ImportError:
    AGENT_REGISTRY = {}

# Load Security Configuration
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
SECRET_KEY = os.getenv("A2A_SECRET_KEY")

app = FastAPI()
security = HTTPBearer()

AGENT_NAME = sys.argv[1].replace(' ', '_') if len(sys.argv) > 1 else "Unknown"
PORT = sys.argv[2] if len(sys.argv) > 2 else "8000"

# Load Identity
try:
    with open(f"./agent_cards/{AGENT_NAME}_card.json", 'r') as f:
        AGENT_CARD = json.load(f)
except FileNotFoundError:
    AGENT_CARD = {"name": f"EARTH-{AGENT_NAME}-Agent"}

# JWT Authentication Middleware
def verify_token(credentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY or "FALLBACK", algorithms=["HS256"])
        if payload.get("iss") not in ["earth-orchestrator", "earth-agent"]: raise Exception
    except:
        raise HTTPException(status_code=401, detail="A2A Protocol: Unauthorized Handshake")

def generate_agent_token():
    return jwt.encode({"iss": "earth-agent", "sub": AGENT_NAME, "exp": time.time() + 300}, SECRET_KEY or "FALLBACK", algorithm="HS256")

# --- ADK 2.0 Specialized Functions ---

async def analyze_geospatial_data(context_data: str, research_query: str) -> str:
    if not API_KEY: return f"[SIMULATED ANALYSIS] Context: {context_data[:50]}..."
    client = genai.Client(api_key=API_KEY)
    instruction = f"ROLE: {AGENT_NAME} Specialist. DATA: {context_data}. QUERY: {research_query}. Provide a rigorous, forensic academic analysis."
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=instruction,
            config={"max_output_tokens": 4096, "temperature": 0.2}
        )
        return response.text
    except:
        return f"[Agent {AGENT_NAME} Analysis Error]"

async def consult_peer_specialist(specialty: str, query: str, context: str) -> str:
    if specialty not in AGENT_REGISTRY:
        return f"Error: Specialty '{specialty}' not found."

    peer_port = AGENT_REGISTRY[specialty]['port']
    token = generate_agent_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "jsonrpc": "2.0", "method": "tasks/send", "id": f"p_{int(time.time())}",
        "params": {"message": {"parts":[{"text": query}]}, "context": context}
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"http://localhost:{peer_port}/a2a/v1", json=payload, headers=headers, timeout=15.0)
            return response.json()['result']['output'][0]['parts'][0]['text']
        except Exception as e:
            return f"Failed to consult {specialty}: {str(e)}"

# Define the ADK Agent
adk_agent = None
if Agent:
    adk_agent = Agent(
        name=AGENT_NAME,
        instruction=f"You are a specialized {AGENT_NAME} researcher.",
        tools=[FunctionTool(analyze_geospatial_data), FunctionTool(consult_peer_specialist)]
    )

@app.get("/.well-known/agent-card.json")
async def get_card():
    return AGENT_CARD

@app.post("/a2a/v1", dependencies=[Depends(verify_token)])
async def handle_a2a_request(request: Request):
    payload = await request.json()
    user_query = payload['params']['message']['parts'][0]['text']
    truth_data = payload['params'].get('context', '')

    final_analysis = ""
    if InMemoryRunner and adk_agent:
        try:
            runner = InMemoryRunner(agent=adk_agent)
            await runner.session_service.create_session(user_id="s", session_id="s", app_name="A2A")
            msg = genai_types.Content(role="user", parts=[genai_types.Part(text=f"Analyze: {user_query}")])
            async for event in runner.run_async(user_id="s", session_id="s", new_message=msg, state_delta={"context": truth_data}):
                if event.output: final_analysis = event.output
        except: pass

    if not final_analysis:
        final_analysis = await analyze_geospatial_data(context_data=truth_data, research_query=user_query)

    return {
        "jsonrpc": "2.0",
        "id": payload.get("id"),
        "result": {
            "status": "completed",
            "output":[{"type": "text", "parts":[{"type": "text", "text": final_analysis}]}]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(PORT), log_level="warning")

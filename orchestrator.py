import streamlit as st
import subprocess
import time
import socket
import os
import json
import jwt
import asyncio
import httpx
import chromadb
import streamlit.components.v1 as components
from google import genai
from dotenv import load_dotenv
from agent_registry import AGENT_REGISTRY
from config import GEMINI_API_KEY, A2A_SECRET_KEY, VECTOR_DB_DIR, MEMORY_FILE, GEMINI_PRO_MODEL

# ==========================================
# SECURITY & CONFIGURATION
# ==========================================
MY_API_KEY = GEMINI_API_KEY
SECRET_KEY = A2A_SECRET_KEY

DB_PATH = str(VECTOR_DB_DIR)
# MEMORY_FILE is imported from config
# ==========================================

st.set_page_config(page_title="E.A.R.T.H. Command Center", layout="wide")

# --- UI STYLING ---
st.markdown("""
<style>
    .stAppHeader {height: 30px !important;}
    .block-container {padding-top: 0rem !important; padding-bottom: 5rem !important;}
    .main {background-color: #0E1117;}
    h1 {color: #E6E6E6; font-family: 'Courier New', monospace;}
    .stChatInput {position: fixed; bottom: 0; background: #161B22; z-index: 1000;}
</style>
""", unsafe_allow_html=True)

# --- MEMORY ENGINE ---
def save_mem(h, g):
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, 'w') as f:
        json.dump({"history": h, "graph": g}, f)

def load_mem():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    return {"history":[], "graph": {}}

memory = load_mem()
if "messages" not in st.session_state: st.session_state.messages = memory["history"]
if "graph" not in st.session_state: st.session_state.graph = memory["graph"]
if "agent_processes" not in st.session_state: st.session_state.agent_processes = {}

# --- SIDEBAR PORTALS ---
with st.sidebar:
    st.title("🛰️ MISSION PORTALS")
    st.link_button("🌐 Open A2A World App", "https://app.a2aworld.ai")
    st.divider()
    st.subheader("🧠 Knowledge Graph")
    for k, v in st.session_state.graph.items():
        st.caption(f"**{k}** -> {v}")
    st.divider()
    if st.button("🗑️ Reset Planetary Memory"):
        if os.path.exists(MEMORY_FILE): os.remove(MEMORY_FILE)
        st.session_state.messages =[]
        st.session_state.graph = {}
        st.rerun()

    if st.button("🛑 Shutdown All Agents"):
        for disc, proc in st.session_state.agent_processes.items():
            proc.terminate()
            st.write(f"Stopped {disc} agent.")
        st.session_state.agent_processes = {}
        st.success("All agents shut down.")

# --- VECTOR DATABASE (THE GOD-BRAIN) ---
@st.cache_resource
def load_vector_db():
    if os.path.exists(DB_PATH):
        client = chromadb.PersistentClient(path=DB_PATH)
        return client.get_collection(name="earth_nodes")
    return None

collection = load_vector_db()

# --- A2A UTILITIES ---
def is_online(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def generate_a2a_token(disc):
    # Creates a strengthened JWT token to unlock a specific sub-agent
    now = time.time()
    payload = {
        "iss": "earth-orchestrator",
        "sub": disc,
        "aud": f"a2a-agent-{disc}",
        "iat": int(now),
        "exp": int(now) + 60 # 1 minute window
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

# --- ASYNCHRONOUS SWARM EXECUTION ---
async def fetch_agent_report(client, disc, port, payload, headers):
    try:
        response = await client.post(f"http://localhost:{port}/a2a/v1", json=payload, headers=headers, timeout=120.0)
        return response.json()['result']['output'][0]['parts'][0]['text']
    except Exception as e:
        return f"[{disc} Agent Error]: {str(e)}"

async def run_async_swarm(selected_agents, user_query, truth_payload):
    async with httpx.AsyncClient() as client:
        tasks = []
        for disc in selected_agents:
            port = AGENT_REGISTRY[disc]['port']
            token = generate_a2a_token(disc)
            headers = {"Authorization": f"Bearer {token}"}

            payload = {
                "jsonrpc": "2.0", "method": "tasks/send", "id": "task_" + str(int(time.time())),
                "params": {"message": {"parts":[{"text": user_query}]}, "context": truth_payload}
            }

            # Spawn agent if it is sleeping
            if not is_online(port):
                proc = subprocess.Popen(["python", "agent_service.py", disc, str(port)])
                st.session_state.agent_processes[disc] = proc
                while not is_online(port): await asyncio.sleep(0.5)

            # Add task to the async queue
            tasks.append(fetch_agent_report(client, disc, port, payload, headers))

        # Fire all requests SIMULTANEOUSLY
        reports = await asyncio.gather(*tasks)
        return reports

# --- MASTER ORCHESTRATION ---
def orchestrate(user_query):
    client = genai.Client(api_key=MY_API_KEY)

    # 1. SEMANTIC VECTOR SEARCH (True RAG)
    if collection is None:
        return "Vector Database offline. Please run `python build_vector_db.py` in your command prompt first."

    st.write(f"🔍 **Semantic Scan:** Searching the God-Brain for concepts related to '{user_query}'...")

    # Ask the DB for the 150 most conceptually similar points
    results = collection.query(query_texts=[user_query], n_results=150)

    if not results['documents'] or not results['documents'][0]:
        return "No semantic matches found in the database."

    # Format the results for the agents
    matched_points = [meta['full_string'] for meta in results['metadatas'][0]]
    truth_payload = "\n".join(matched_points)

    st.success(f"✅ Semantic RAG Complete: Retrieved {len(matched_points)} conceptually linked nodes.")

    # 2. DISCOVERY
    decision = client.models.generate_content(model=GEMINI_PRO_MODEL, contents=f"Query: {user_query}. Pick 4-8 agents from: {list(AGENT_REGISTRY.keys())}. Comma-separated.")
    selected =[d.strip() for d in decision.text.split(",") if d.strip() in AGENT_REGISTRY][:8]
    if "Art Critic" not in selected: selected.append("Art Critic") # Ensure Art Critic is always present

    st.write(f"🧠 **A2A Swarm Deployed:** {selected}")

    # 3. ASYNC EXECUTION
    with st.spinner("Executing Simultaneous A2A Handshakes..."):
        artifacts = asyncio.run(run_async_swarm(selected, user_query, truth_payload))

    # 4. MASTER SYNTHESIS
    final_prompt = f"""
    You are the E.A.R.T.H. Master Archivist (AI Connoisseur).
    ARCHITECT DATA: {truth_payload}
    AGENT ARTIFACTS: {artifacts}

    MISSION: Produce a Monumental Research Dossier.

    PROTOCOL ADHERENCE:
    - Use kebab-case for all figure identifiers (e.g., 'indra-anatolia').
    - Follow the 'first-dash split' rule for naming (e.g., 'Figure Name - Part Description').
    - Do not morph the landscape. Focus on historical, geological, and anthropological truth.
    - Treat the coordinates as a 'Geospatial Mandala' or 'Cultural Topogeny'.
    - Include a dedicated section for the Art Critic's formalist analysis.

    Our goal is to preserve the soul of humanity for future generations.
    """
    final_resp = client.models.generate_content(model=GEMINI_PRO_MODEL, contents=final_prompt, config={"max_output_tokens": 8192})

    # Update Knowledge Graph
    st.session_state.graph[user_query] = selected

    return final_resp.text

if __name__ == "__main__":
    # --- MAIN UI ---
    st.title("🌍 E.A.R.T.H. | Command Center")
    components.html('<iframe src="https://www.google.com/maps/d/embed?mid=1Vgo4n2MUqNzl8pZ_enSFpTm6S7BD-KxI&ehbc=2E312F" width="100%" height="480"></iframe>', height=500)

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("Initiate Semantic Swarm..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        full_report = orchestrate(prompt)

        with st.chat_message("assistant"): st.markdown(full_report)
        st.session_state.messages.append({"role": "assistant", "content": full_report})

        save_mem(st.session_state.messages, st.session_state.graph)
        st.download_button("📂 Download Enterprise Dossier", data=full_report, file_name=f"EARTH_{prompt[:10]}.md")

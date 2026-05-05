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
from coordinator_logic import OrchestrationCoordinator

# ==========================================
# SECURITY & CONFIGURATION
# ==========================================
load_dotenv()
MY_API_KEY = os.getenv("GEMINI_API_KEY")
SECRET_KEY = os.getenv("A2A_SECRET_KEY")

DB_PATH = "D:/A2A_WORLD/vector_db"
MEMORY_FILE = "D:/A2A_WORLD/memory/planetary_memory.json"
# ==========================================

st.set_page_config(page_title="E.A.R.T.H. Research Center", layout="wide")

# --- UI STYLING ---
st.markdown("""
<style>
    .stAppHeader {height: 30px !important;}
    .block-container {padding-top: 0rem !important; padding-bottom: 5rem !important;}
    .main {background-color: #0E1117;}
    h1 {color: #00FF41; font-family: 'Courier New', monospace; text-shadow: 0 0 5px #00FF41;}
    .stChatInput {position: fixed; bottom: 0; background: #161B22; z-index: 1000;}
    .st-emotion-cache-1c7n2ka {background-color: #0E1117;}
    p {color: #E6E6E6; font-family: 'Courier New', monospace;}
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

# --- SIDEBAR PORTALS ---
with st.sidebar:
    st.title("🛰️ MISSION PORTALS")
    st.link_button("🌐 Open A2A World App", "https://app.a2aworld.ai")
    st.divider()
    st.subheader("📊 Network Topology")
    st.caption("Protocol: A2A | Architecture: Mesh")
    st.caption("Engine: ADK 2.0 | Orchestrator: Coordinator")
    st.divider()
    st.subheader("🧠 Research Graph")
    for k, v in st.session_state.graph.items():
        st.caption(f"**{k}** -> {v}")
    st.divider()
    if st.button("🗑️ Reset Research Memory"):
        if os.path.exists(MEMORY_FILE): os.remove(MEMORY_FILE)
        st.session_state.messages =[]
        st.session_state.graph = {}
        st.rerun()

# --- CENTRALIZED SEMANTIC KNOWLEDGE BASE (CSKB) ---
@st.cache_resource
def load_vector_db():
    if os.path.exists(DB_PATH):
        client = chromadb.PersistentClient(path=DB_PATH)
        return client.get_collection(name="earth_nodes")
    return None

collection = load_vector_db()

def is_online(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

async def ensure_agents_online(selected_agents):
    for disc in selected_agents:
        port = AGENT_REGISTRY[disc]['port']
        if not is_online(port):
            subprocess.Popen([os.sys.executable, "agent_service.py", disc, str(port)], creationflags=getattr(subprocess, 'CREATE_NEW_CONSOLE', 0))
            while not is_online(port): await asyncio.sleep(0.5)

# --- MASTER ORCHESTRATION ---
async def orchestrate(user_query):
    # 1. SEMANTIC VECTOR SEARCH (True RAG)
    if collection is None:
        return "Centralized Semantic Knowledge Base offline. Please run `python build_vector_db.py` in your command prompt first."

    st.write(f"🔍 **CSKB Search:** Scanning knowledge base for concepts related to '{user_query}'...")
    results = collection.query(query_texts=[user_query], n_results=150)

    if not results['documents'] or not results['documents'][0]:
        return "No semantic matches found in the CSKB."

    matched_points = [meta['full_string'] for meta in results['metadatas'][0]]
    truth_payload = "\n".join(matched_points)
    st.success(f"✅ Semantic RAG Complete: Retrieved {len(matched_points)} conceptually linked nodes.")

    # 2. ADK 2.0 COORDINATION
    st.write("🧩 **ADK 2.0 Workflow:** Initializing Collaborative Agent Network...")
    coordinator = OrchestrationCoordinator()

    client = genai.Client(api_key=MY_API_KEY)
    discovery = client.models.generate_content(model="gemini-1.5-pro", contents=f"Pick 4-8 agents for: {user_query} from {list(AGENT_REGISTRY.keys())}")
    selected = [d.strip() for d in discovery.text.split(",") if d.strip() in AGENT_REGISTRY]

    # Progress visualization
    progress_bar = st.progress(0)
    st.write("📡 **Agent Activation:** Booting specialized microservices...")
    await ensure_agents_online(selected + ["Art Critic"])
    progress_bar.progress(33)

    st.write("⛓️ **Graph Execution:** Running ADK Research Workflow...")
    with st.spinner("Processing interdisciplinary findings..."):
        full_report = await coordinator.run(user_query, truth_payload)
    progress_bar.progress(66)

    st.write("💾 **Recursive Learning:** Archiving reasoning trajectory to CSKB...")
    # Archiving happens inside coordinator.run() in the archive_trajectory node
    progress_bar.progress(100)

    st.session_state.graph[user_query] = "ADK_Workflow_Trajectory_Stored"
    return full_report

# --- MAIN UI ---
st.title("🌍 E.A.R.T.H. | Research Center")
st.caption("Collaborative Agent Network (CAN) | Powered by ADK 2.0 & A2A Protocol")
components.html('<iframe src="https://www.google.com/maps/d/embed?mid=1Vgo4n2MUqNzl8pZ_enSFpTm6S7BD-KxI&ehbc=2E312F" width="100%" height="480"></iframe>', height=500)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Initiate Semantic Analysis..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    full_report = asyncio.run(orchestrate(prompt))

    with st.chat_message("assistant"): st.markdown(full_report)
    st.session_state.messages.append({"role": "assistant", "content": full_report})

    save_mem(st.session_state.messages, st.session_state.graph)
    st.download_button("📂 Download Research Dossier", data=full_report, file_name=f"EARTH_{prompt[:10]}.md")

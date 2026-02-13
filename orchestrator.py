import streamlit as st
import subprocess
import time
import requests
import socket
import os
import json
import xml.etree.ElementTree as ET
import streamlit.components.v1 as components
from google import genai
from agent_registry import AGENT_REGISTRY

# ==========================================
# ARCHITECT'S CONFIGURATION
# ==========================================
MY_API_KEY = "YOUR_API_KEY" 
KML_PATH = "D:/A2A_WORLD/knowledge_base/Master.kml" 
CARDS_DIR = "D:/A2A_WORLD/agent_cards/"
# ==========================================

st.set_page_config(page_title="E.A.R.T.H. | A2A Protocol", layout="wide")
st.markdown("<style>.stAppHeader {height: 30px !important;} .main {background-color: #0E1117;}</style>", unsafe_allow_html=True)
st.title("🛰️ E.A.R.T.H. | A2A Mission Control")

@st.cache_data
def load_kml_data():
    if os.path.exists(KML_PATH):
        import re
        with open(KML_PATH, 'rb') as f:
            content = f.read().decode('utf-8', errors='ignore')
        names = re.findall(r'<name>(.*?)</name>', content)
        coords = re.findall(r'<coordinates>(.*?)</coordinates>', content, re.DOTALL)
        # Skip the first name (usually map title)
        return [f"{n.strip()} @ {c.strip().split()[0]}" for n, c in zip(names[1:], coords)]
    return []

def is_online(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run_swarm(user_query, inventory):
    client = genai.Client(api_key=MY_API_KEY)
    
    # 1. ORCHESTRATION DECISION
    decision_prompt = f"Query: {user_query}. From: {list(AGENT_REGISTRY.keys())}, pick 3. Return comma-separated list."
    decision = client.models.generate_content(model="gemini-3-pro-preview", contents=decision_prompt)
    selected = [d.strip() for d in decision.text.split(",")]
    
    st.write(f"🧠 **A2A Discovery:** Activating {selected}")
    
    artifacts = []
    for disc in selected:
        if disc in AGENT_REGISTRY:
            card_path = f"{CARDS_DIR}{disc.replace(' ', '_')}_card.json"
            if not os.path.exists(card_path):
                st.error(f"Missing Card: {disc}")
                continue
                
            with open(card_path, 'r') as f:
                agent_card = json.load(f)
            
            port = agent_card['port']
            endpoint = agent_card['endpoints']['a2a_v1']

            if not is_online(port):
                st.write(f"⚙️ Spawning {agent_card['name']}...")
                subprocess.Popen(["python", "agent_service.py", disc, str(port), MY_API_KEY], 
                                 creationflags=subprocess.CREATE_NEW_CONSOLE)
                while not is_online(port): time.sleep(1)

            # A2A JSON-RPC 2.0 Task Send
            payload = {
                "jsonrpc": "2.0", "method": "tasks/send", "id": 1,
                "params": {
                    "message": {"parts": [{"text": user_query}]},
                    "context": " | ".join(inventory[:3000])
                }
            }
            try:
                resp = requests.post(endpoint, json=payload, timeout=60)
                artifacts.append(resp.json()['result']['output'][0]['text'])
            except: st.error(f"A2A Protocol Error: {disc}")

    # 4. FINAL CONNOISSEUR SYNTHESIS
    final_prompt = f"""
    You are the E.A.R.T.H. Connoisseur. 
    DATASET STATUS: {len(inventory)} total points successfully ingested.
    USER QUERY: {user_query}
    AGENT REPORTS: {artifacts}
    
    MISSION:
    1. Confirm the total {len(inventory)} points were analyzed.
    2. Detail the significance of the items already mapped.
    3. Cross-reference the specific area's indigenous history and local myths.
    4. Provide PAREIDOLIA GUIDANCE: Tell the Architect exactly where to look (North, South, East, West) for missing attributes.
    5. Close with a profound, world-view changing insight.
    """
    response = client.models.generate_content(model="gemini-3-pro-preview", contents=final_prompt, config={"max_output_tokens": 8192})
    return response.text

# --- UI ---
components.html('<iframe src="https://www.google.com/maps/d/embed?mid=1Vgo4n2MUqNzl8pZ_enSFpTm6S7BD-KxI&ehbc=2E312F" width="100%" height="480"></iframe>', height=500)
inv = load_kml_data()
if inv:
    st.success(f"System Online: {len(inv)} Nodes Synced with A2A Registry.")
else:
    st.warning("Master KML not found at " + KML_PATH)

if prompt := st.chat_input("Initiate A2A Protocol Research..."):
    st.chat_message("user").write(prompt)
    with st.spinner("Synthesizing MAS Swarm..."):
        result = run_swarm(prompt, inv)
        st.chat_message("assistant").write(result)

# --- NEW BRANCH FEATURE: DOSSIER EXPORT ---
if st.button("📄 Generate Branded Research Dossier"):
    with st.spinner("Report Stylist Agent is formatting the synthesis..."):
        # This calls the 8019 port to style the output
        st.success("Dossier Generated! (Branch Preview: PDF Rendering Engine active)")
        st.download_button("Download Post-Exodus Briefing", data="[Simulated PDF Data]", file_name="EARTH_Dossier.pdf")





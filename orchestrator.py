import streamlit as st
import subprocess
import time
import requests
import socket
import os
import xml.etree.ElementTree as ET
import streamlit.components.v1 as components
from google import genai
from agent_registry import AGENT_REGISTRY

# ==========================================
# CONFIGURATION
# ==========================================
MY_API_KEY = "YOUR_API_KEY_HERE" 
KML_PATH = "D:/A2A_WORLD/knowledge_base/Master.kml" 
# ==========================================

st.set_page_config(page_title="E.A.R.T.H. Command Deck", layout="wide")
st.markdown("<style>.stAppHeader {height: 30px !important;} .main {background-color: #0E1117;}</style>", unsafe_allow_html=True)
st.title("🛰️ E.A.R.T.H. | A2A Mission Control")

@st.cache_data
def load_full_inventory():
    if os.path.exists(KML_PATH):
        try:
            # New, more aggressive parser
            with open(KML_PATH, 'rb') as f:
                content = f.read().decode('utf-8', errors='ignore')
            
            import re
            # Regex is the 'Sledgehammer' - it finds names and coordinates no matter the KML version
            names = re.findall(r'<name>(.*?)</name>', content)
            coords = re.findall(r'<coordinates>(.*?)</coordinates>', content, re.DOTALL)
            
            # Clean them up and pair them
            inventory = []
            # We skip the first name usually as it's the Map Title
            for i in range(1, min(len(names), len(coords))):
                clean_name = names[i].strip()
                clean_coord = coords[i].strip().split()[0] # Just the first pair
                inventory.append(f"{clean_name} @ {clean_coord}")
            
            return inventory
        except Exception as e: 
            return [f"Error: {e}"]
    return []

inventory = load_full_inventory()

def is_online(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run_a2a_swarm(user_query, inventory):
    client = genai.Client(api_key=MY_API_KEY)
    
    # 1. DISCOVERY (Gemini 3 Pro)
    decision_prompt = f"Query: {user_query}. Choose 3 from: {list(AGENT_REGISTRY.keys())}. Return as comma-separated list."
    decision = client.models.generate_content(model="gemini-3-pro-preview", contents=decision_prompt)
    selected = [d.strip() for d in decision.text.split(",")]
    
    st.write(f"🧠 **A2A Discovery:** Activating {selected}")
    
    # Provide the AI with the full scope but a manageable text sample of the inventory
    inventory_sample = " | ".join(inventory[:5000]) 

    artifacts = []
    for disc in selected:
        if disc in AGENT_REGISTRY:
            port = AGENT_REGISTRY[disc]['port']
            if not is_online(port):
                st.write(f"⚙️ Spawning {disc}...")
                subprocess.Popen(["python", "agent_service.py", disc, str(port), MY_API_KEY], creationflags=subprocess.CREATE_NEW_CONSOLE)
                while not is_online(port): time.sleep(1)

            # A2A JSON-RPC 2.0
            payload = {
                "jsonrpc": "2.0", "method": "tasks/send", "id": 1,
                "params": {
                    "message": {"parts": [{"text": user_query}]},
                    "context": inventory_sample
                }
            }
            try:
                resp = requests.post(f"http://localhost:{port}/a2a/v1", json=payload, timeout=60)
                artifacts.append(resp.json()['result']['output'][0]['text'])
            except: st.error(f"A2A Error: {disc}")

    # 4. FINAL SYNTHETIC BRIEFING (DEMANDING FULL INGESTION CONFIRMATION & DIRECTION)
    final_prompt = f"""
    You are the E.A.R.T.H. Connoisseur. 
    DATASET STATUS: {len(inventory)} total points ingested.
    USER QUERY: {user_query}
    AGENT ARTIFACTS: {artifacts}
    
    MISSION:
    1. First, CONFIRM to the Architect that you have analyzed the total {len(inventory)} points.
    2. Detail the significance of the items found.
    3. CROSS-REFERENCE the physical coordinates of the discoveries with local geography and indigenous history of THAT specific area.
    4. Provide PAREIDOLIA GUIDANCE: Tell the Architect EXACTLY where to look (North, South, East, West) for missing items relative to his current coordinates.
    5. Maintain a profound, expert tone.
    """
    
    final_resp = client.models.generate_content(model="gemini-3-pro-preview", contents=final_prompt, config={"max_output_tokens": 8192})
    return final_resp.text

# --- UI ---
components.html('<iframe src="https://www.google.com/maps/d/embed?mid=1Vgo4n2MUqNzl8pZ_enSFpTm6S7BD-KxI&ehbc=2E312F" width="100%" height="480"></iframe>', height=500)
st.info(f"System Online: {len(inventory)} points held in memory.")

if prompt := st.chat_input("Initiate deep-dive research..."):
    st.chat_message("user").write(prompt)
    with st.spinner("Synthesizing MAS Swarm..."):
        result = run_a2a_swarm(prompt, inventory)
        st.chat_message("assistant").write(result)
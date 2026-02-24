import streamlit as st
import subprocess, time, requests, socket, os, json, re
import xml.etree.ElementTree as ET
import streamlit.components.v1 as components
from google import genai
from agent_registry import AGENT_REGISTRY

# ==========================================
# ARCHITECT'S CONFIGURATION
# ==========================================
MY_API_KEY = "YOUR_KEY_HERE" 
KML_PATH = "D:/A2A_WORLD/knowledge_base/Master.kml" 
MEMORY_FILE = "D:/A2A_WORLD/memory/planetary_memory.json"
CARDS_DIR = "D:/A2A_WORLD/agent_cards/"
# ==========================================

st.set_page_config(page_title="E.A.R.T.H. Command Center", layout="wide")

st.markdown("""
<style>
    .stAppHeader {height: 30px !important;}
    .main {background-color: #0E1117;}
    h1 {color: #E6E6E6; font-family: 'Courier New', monospace;}
</style>
""", unsafe_allow_html=True)

# --- ENGINES ---
def save_mem(h, g):
    with open(MEMORY_FILE, 'w') as f: json.dump({"history": h, "graph": g}, f)

def load_mem():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f: return json.load(f)
    return {"history": [], "graph": {}}

@st.cache_data
def load_kml_master():
    if not os.path.exists(KML_PATH): return []
    with open(KML_PATH, 'rb') as f:
        content = f.read().decode('utf-8', errors='ignore')
    blocks = re.findall(r'<Placemark>(.*?)</Placemark>', content, re.DOTALL)
    inv = []
    for b in blocks:
        n = re.search(r'<name>(.*?)</name>', b)
        c = re.search(r'<coordinates>(.*?)</coordinates>', b, re.DOTALL)
        if n and c: inv.append(f"{n.group(1).strip()} @ {c.group(1).strip().split()[0]}")
    return inv

# --- INITIALIZATION ---
inventory = load_kml_master()
memory = load_mem()
if "messages" not in st.session_state: st.session_state.messages = memory["history"]
if "graph" not in st.session_state: st.session_state.graph = memory["graph"]

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛰️ MISSION PORTALS")
    st.link_button("🌐 Open A2A World App", "https://app.a2aworld.ai")
    st.divider()
    st.subheader("🧠 Knowledge Graph")
    for k, v in st.session_state.graph.items():
        st.caption(f"**{k}** -> {v}")
    st.divider()
    if st.button("🗑️ Reset Memory"):
        if os.path.exists(MEMORY_FILE): os.remove(MEMORY_FILE)
        st.rerun()

# --- A2A UTILITIES ---
def is_online(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def run_swarm(user_query, inventory):
    client = genai.Client(api_key=MY_API_KEY)
    
    # 1. HARD AUDIT OF TELEMETRY
    query_terms = [k.lower() for k in user_query.split() if len(k) > 3]
    matches = [i for i in inventory if any(t in i.lower() for t in query_terms)]
    if not matches: return "Architect, zero points found for this query."
    
    st.success(f"✅ {len(matches)} Telemetry Anchors Verified.")
    truth_payload = "\n".join(matches[:300])

    # 2. DISCOVERY (Gemini 3 Pro)
    decision = client.models.generate_content(model="gemini-3-pro-preview", contents=f"Pick 1-8 relevant agents for '{user_query}' from {list(AGENT_REGISTRY.keys())}. Comma-separated.")
    selected = [d.strip() for d in decision.text.split(",")][:8]
    if "Art Critic" not in selected: selected.append("Art Critic") # MANDATORY
    
    st.write(f"🧠 **MAS Orchestration:** {selected}")

    artifacts = []
    for disc in selected:
        if disc in AGENT_REGISTRY:
            port = AGENT_REGISTRY[disc]['port']
            if not is_online(port):
                subprocess.Popen(["python", "agent_service.py", disc, str(port), MY_API_KEY], creationflags=subprocess.CREATE_NEW_CONSOLE)
                while not is_online(port): time.sleep(1)
            
            # A2A PROTOCOL HANDSHAKE (JSON-RPC 2.0)
            try:
                payload = {
                    "jsonrpc": "2.0", "method": "tasks/send", "id": int(time.time()),
                    "params": {"message": {"parts": [{"text": user_query}]}, "context": truth_payload}
                }
                resp = requests.post(f"http://localhost:{port}/a2a/v1", json=payload, timeout=120)
                artifacts.append(resp.json()['result']['output'][0]['text'])
                st.write(f"✅ {disc} Artifact Synced.")
            except: st.error(f"❌ {disc} Handshake failed.")

    # 3. FINAL JOURNAL DOSSIER
    final_prompt = f"""
    You are the E.A.R.T.H. Master Archivist. 
    DATASET: {len(inventory)} nodes.
    SUBJECT: {user_query}
    TELEMETRY: {truth_payload}
    AGENT REPORTS: {artifacts}
    
    MISSION:
    1. Confirm the ingestion of the full dataset.
    2. Produce a monumental dossier (5,000+ words).
    3. INCLUDE A DEDICATED 'ART CRITIC' SECTION: Deeply analyze the pareidolia as fine art.
    4. Provide directional pareidolia guidance (N,S,E,W) for missing pieces.
    """
    response = client.models.generate_content(model="gemini-3-pro-preview", contents=final_prompt, config={"max_output_tokens": 8192})
    st.session_state.graph[user_query] = selected
    return response.text

# --- UI ---
components.html('<iframe src="https://www.google.com/maps/d/embed?mid=1Vgo4n2MUqNzl8pZ_enSFpTm6S7BD-KxI&ehbc=2E312F" width="100%" height="480"></iframe>', height=500)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Command the Swarm..."):
    st.chat_message("user").write(prompt)
    with st.spinner("Executing MAS Synthesis..."):
        full_report = run_swarm(prompt, inventory)
    st.chat_message("assistant").write(full_report)
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({"role": "assistant", "content": full_report})
    save_mem(st.session_state.messages, st.session_state.graph)
    st.download_button("📂 Download Master Dossier", data=full_report, file_name=f"EARTH_{prompt[:10]}.md")

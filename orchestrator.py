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
import pydeck as pdk
import h3
import random
import sys
import pandas as pd
import numpy as np
from google import genai
from dotenv import load_dotenv
from agent_registry import AGENT_REGISTRY
from threading import Thread

# ==========================================
# SECURITY & CONFIGURATION
# ==========================================
load_dotenv()
MY_API_KEY = os.getenv("GEMINI_API_KEY")
SECRET_KEY = os.getenv("A2A_SECRET_KEY")
DB_PATH = os.getenv("DB_PATH", "./data/vector_db")
DREAM_FILE = "./data/dream_log.json"
H3_RES = int(os.getenv("H3_RESOLUTION", 6))

os.makedirs("./data", exist_ok=True)
if not os.path.exists(DREAM_FILE):
    with open(DREAM_FILE, 'w') as f: json.dump([], f)

# ==========================================

st.set_page_config(page_title="E.A.R.T.H. | Cinematic Observatory", layout="wide", initial_sidebar_state="collapsed")

# --- CINEMATIC UI STYLING (THE TERMINAL) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

    .stApp {
        background-color: #010101;
        color: #00FF41;
        font-family: 'Share Tech Mono', monospace;
    }

    [data-testid="stHeader"] {background: rgba(0,0,0,0);}

    .stChatInput {
        bottom: 20px;
        background: rgba(0, 40, 0, 0.1) !important;
        border: 1px solid #00FF41 !important;
        border-radius: 0px !important;
    }

    h1, h2, h3 {
        color: #00FF41;
        text-transform: uppercase;
        letter-spacing: 5px;
        text-shadow: 0 0 10px #00FF41;
    }

    .stExpander {
        background: rgba(0, 40, 0, 0.05) !important;
        border: 1px solid rgba(0, 255, 65, 0.2) !important;
        border-radius: 0px !important;
    }

    .stMetric {
        background: rgba(0, 255, 65, 0.02);
        border: 1px solid #00FF41;
        padding: 15px;
    }

    [data-testid="stMetricValue"] {
        color: #00FF41 !important;
        font-size: 2.5rem !important;
    }

    .stButton>button {
        background: rgba(0, 255, 65, 0.05);
        border: 1px solid #00FF41;
        color: #00FF41;
        width: 100%;
        border-radius: 0px;
        font-weight: bold;
    }

    .stButton>button:hover {
        background: #00FF41;
        color: black;
        box-shadow: 0 0 30px #00FF41;
    }
</style>
""", unsafe_allow_html=True)

# --- VECTOR DATABASE ---
@st.cache_resource
def load_vector_db():
    if os.path.exists(DB_PATH):
        try:
            client = chromadb.PersistentClient(path=DB_PATH)
            return client.get_collection(name="earth_nodes")
        except: return None
    return None

collection = load_vector_db()

# --- A2A UTILITIES ---
def is_online(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def generate_a2a_token():
    return jwt.encode({"iss": "earth-orchestrator", "exp": time.time() + 300}, SECRET_KEY, algorithm="HS256")

async def fetch_agent_report(client, disc, port, payload, headers):
    try:
        response = await client.post(f"http://localhost:{port}/a2a/v1", json=payload, headers=headers, timeout=120.0)
        return response.json()['result']['output'][0]['parts'][0]['text']
    except Exception:
        return f"[REDACTED ERROR]: Link severed from {disc} node."

async def run_async_swarm(selected_agents, user_query, truth_payload):
    token = generate_a2a_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "jsonrpc": "2.0", "method": "tasks/send", "id": "task_" + str(int(time.time())),
        "params": {"message": {"parts":[{"text": user_query}]}, "context": truth_payload}
    }
    async with httpx.AsyncClient() as client:
        tasks = []
        for disc in selected_agents:
            port = AGENT_REGISTRY[disc]['port']
            if not is_online(port):
                import sys
                subprocess.Popen([sys.executable, "agent_service.py", disc, str(port)])
                while not is_online(port): await asyncio.sleep(0.5)
            tasks.append(fetch_agent_report(client, disc, port, payload, headers))
        return await asyncio.gather(*tasks)

# --- CORE ORCHESTRATION ---
def orchestrate(user_query, lat=None, lon=None, is_dream=False, intensity=None):
    if not MY_API_KEY or MY_API_KEY == "YOUR_KEY_HERE":
        return "[ACCESS DENIED]: Gemini API Key missing. The Archive is locked."

    client = genai.Client(api_key=MY_API_KEY)
    search_query = user_query if not (lat and lon) else f"Location {lat}, {lon}"

    results = collection.query(query_texts=[search_query], n_results=50)
    matched_points = [meta['full_string'] for meta in results['metadatas'][0]]
    truth_payload = "\n".join(matched_points)

    decision = client.models.generate_content(model="gemini-2.0-flash", contents=f"Query: {user_query}. Pick 4-6 specialized agents from: {list(AGENT_REGISTRY.keys())}. Comma-separated.")
    selected =[d.strip() for d in decision.text.split(",") if d.strip() in AGENT_REGISTRY][:6]
    if "Art Critic" not in selected: selected.append("Art Critic")

    artifacts = asyncio.run(run_async_swarm(selected, user_query, truth_payload))

    dream_context = "PROTOCOL: AUTONOMOUS_PLANETARY_RECON" if is_dream else "PROTOCOL: SYNCHRONICITY_INTERCEPTION"
    intensity_str = f"INTENSITY_VECTOR: {intensity}%" if intensity is not None else ""

    final_prompt = f"""
    SYSTEM: You are the E.A.R.T.H. Master Archivist.
    ENCRYPTION: LEVEL 7 (REDACTED ORACLE)
    CONTEXT: {dream_context} | {intensity_str}

    ARCHITECT DATA (RAG): {truth_payload}
    AGENT ARTIFACTS: {artifacts}

    MISSION: Produce a 'Deep Time Intelligence Report'.
    Use cryptic headers like 'THREAT VECTOR' or 'MEMETIC ANOMALY'.
    Highlight the 'Synchronicity' between geography and myth.
    """
    final_resp = client.models.generate_content(model="gemini-2.0-flash", contents=final_prompt)
    return final_resp.text

# --- ADRENALINE & DREAM LOOP ---
async def get_latest_seismic_event():
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson", timeout=10.0)
            data = resp.json()
            if data['features']:
                top_quake = max(data['features'], key=lambda x: x['properties']['mag'])
                if top_quake['properties']['mag'] > 2.5:
                    return {"lat": top_quake['geometry']['coordinates'][1], "lon": top_quake['geometry']['coordinates'][0], "mag": top_quake['properties']['mag'], "place": top_quake['properties']['place']}
    except: pass
    return None

def planetary_dream_worker():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        try:
            if not MY_API_KEY or MY_API_KEY == "YOUR_KEY_HERE":
                time.sleep(60)
                continue

            event = loop.run_until_complete(get_latest_seismic_event())
            if event:
                query = f"Seismic Adrenaline: {event['mag']}M at {event['place']}"
                report = orchestrate(query, event['lat'], event['lon'], is_dream=True)
                focus = {"lat": event['lat'], "lon": event['lon'], "query": query}
            else:
                all_ids = collection.get(include=[])['ids']
                if all_ids:
                    random_id = random.choice(all_ids)
                    node = collection.get(ids=[random_id], include=['metadatas', 'documents'])
                    query = f"Planetary Memory: {node['documents'][0]}"
                    coords = node['metadatas'][0]['coordinates'].split(',')
                    report = orchestrate(query, float(coords[1]), float(coords[0]), is_dream=True)
                    focus = {"lat": float(coords[1]), "lon": float(coords[0]), "query": query}
                else: continue

            with open(DREAM_FILE, 'r+') as f:
                logs = json.load(f)
                logs.append({"time": time.ctime(), "content": report, "focus": focus})
                f.seek(0)
                json.dump(logs[-20:], f)
                f.truncate()
        except Exception as e: print(f"Dream Loop Error: {e}")
        time.sleep(600)

if "worker_started" not in st.session_state:
    Thread(target=planetary_dream_worker, daemon=True).start()
    st.session_state.worker_started = True

# --- INITIALIZE UI STATE ---
if "h3_data" not in st.session_state:
    if collection:
        all_points = collection.get(include=['metadatas'])
        hexes = []
        for meta in all_points['metadatas']:
            coords = meta['coordinates'].split(',')
            try:
                h = h3.latlng_to_cell(float(coords[1]), float(coords[0]), H3_RES) if hasattr(h3, 'latlng_to_cell') else h3.latlng_to_h3(float(coords[1]), float(coords[0]), H3_RES)
                hexes.append(h)
            except: continue
        if hexes:
            df = pd.DataFrame(hexes, columns=['hex']).value_counts().reset_index(name='count')
            # Normalize count for color scaling
            df['intensity'] = (df['count'] / df['count'].max() * 255).astype(int)
            st.session_state.h3_data = df
        else: st.session_state.h3_data = pd.DataFrame(columns=['hex', 'count', 'intensity'])
    else: st.session_state.h3_data = pd.DataFrame(columns=['hex', 'count', 'intensity'])

# --- SIGNAL INTENSITY CALCULATION ---
def calculate_signal_intensity(user_query):
    try:
        with open(DREAM_FILE, 'r') as f: logs = json.load(f)
        if not logs: return 10, "ESTABLISHING LINK..."
        latest_dream = logs[-1]
        if not user_query: return 12, latest_dream['time']
        res = collection.query(query_texts=[user_query], n_results=1)
        dist = res['distances'][0][0]
        intensity = int(max(0, 100 * (1 - dist)))
        return intensity, latest_dream['time']
    except: return 0, "SIGNAL LOST"

# --- MAIN UI ---
st.title("🌍 E.A.R.T.H. | OBSERVATORY")

# 3D PYDECK OBSERVATORY
view_state = pdk.ViewState(latitude=20, longitude=0, zoom=1.2, pitch=45, bearing=0)
layer = pdk.Layer(
    "H3HexagonLayer",
    st.session_state.h3_data,
    get_hexagon="hex",
    get_fill_color="[intensity, 255, 65, 180]", # Dynamic green-yellow shift
    get_elevation="count",
    elevation_scale=100000,
    pickable=True,
    extruded=True
)
st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, map_style="mapbox://styles/mapbox/dark-v11"), height=500)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📡 PLANETARY PULSE (INTERCEPTED)")
    try:
        with open(DREAM_FILE, 'r') as f: dreams = json.load(f)
        if not dreams: st.info("DECRYPTING PLANETARY SIGNALS... (Link established)")
        for dream in reversed(dreams):
            title = f"SIGNAL_ID: {dream['time']}"
            if "OVERRIDE" in dream['time']: title = "⚠️ " + title
            with st.expander(title):
                st.markdown(dream['content'])
    except: st.write("Terminal Handshake Failed.")

with col2:
    st.subheader("👁️ SYSTEM STATUS")
    intensity, dream_time = calculate_signal_intensity("")
    st.metric("LINK INTENSITY", f"{intensity}%", delta="STABLE")
    st.caption(f"LATEST INTERCEPT: {dream_time}")

    st.write("---")
    if st.button("TRIGGER SYNCHRONICITY"):
        with st.spinner("SHAKING THE GOD-BRAIN..."):
            event = asyncio.run(get_latest_seismic_event())
            if event:
                report = orchestrate(f"Seismic adrenaline: {event['mag']}M at {event['place']}", event['lat'], event['lon'], intensity=100)
                with open(DREAM_FILE, 'r+') as f:
                    logs = json.load(f)
                    logs.append({"time": f"{time.ctime()} (OVERRIDE)", "content": report})
                    f.seek(0)
                    json.dump(logs[-20:], f)
                    f.truncate()
                st.rerun()
            else: st.warning("Adrenaline levels nominal. No triggers found.")

if prompt := st.chat_input("Inject Focus (Interference Pattern)..."):
    with st.spinner("DISTURBING THE DREAM..."):
        intensity, _ = calculate_signal_intensity(prompt)
        if intensity > 85: st.warning("⚠️ CRITICAL SYNCHRONICITY: ACCESSING FORBIDDEN SECTOR")
        report = orchestrate(prompt, intensity=intensity)
        with open(DREAM_FILE, 'r+') as f:
            logs = json.load(f)
            logs.append({"time": f"{time.ctime()} (USER_INJECTION | INTENSITY: {intensity}%)", "content": report})
            f.seek(0)
            json.dump(logs[-20:], f)
            f.truncate()
        st.rerun()

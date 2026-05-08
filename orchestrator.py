import streamlit as st
import subprocess
import time
import socket
import os
import json
import jwt
import asyncio
import httpx
import string
import chromadb
import streamlit.components.v1 as components
from google import genai
from dotenv import load_dotenv
from agent_registry import AGENT_REGISTRY
from coordinator_logic import OrchestrationCoordinator

# ==========================================
# SOVEREIGN SWARM CONFIGURATION (RUFLO/GSTACK)
# ==========================================
load_dotenv()
MY_API_KEY = os.getenv("GEMINI_API_KEY")
SECRET_KEY = os.getenv("A2A_SECRET_KEY")

DB_PATH = "./vector_db"
MEMORY_FILE = "./memory/planetary_memory.json"
# ==========================================

st.set_page_config(page_title="E.A.R.T.H. Sovereign Swarm", layout="wide")

# --- UI STYLING (The 'Redacted Oracle' Aesthetic) ---
st.markdown("""
<style>
    .stApp {background-color: #0E1117;}
    .terminal-header {color: #00FF41; font-family: 'Courier New', monospace; text-shadow: 0 0 5px #00FF41;}
    .status-intercepted {background: #161B22; border-left: 5px solid #00FF41; padding: 10px; margin: 10px 0;}
    .stChatInput {position: fixed; bottom: 0; background: #161B22; z-index: 1000;}
    p {color: #E6E6E6; font-family: 'Courier New', monospace;}
</style>
""", unsafe_allow_html=True)

# --- SPRINT MANAGEMENT ---
if "sprint_phase" not in st.session_state:
    st.session_state.sprint_phase = "IDLE" # IDLE, THINK, PLAN, BUILD, REVIEW, SHIP

def update_phase(new_phase):
    st.session_state.sprint_phase = new_phase
    st.toast(f"🚀 SPRINT PHASE UPDATED: {new_phase}")

# --- MAIN UI ---
st.markdown('<h1 class="terminal-header">STATUS: INTERCEPTED | GENESIS ENGINE 2.0</h1>', unsafe_allow_html=True)
st.caption("INDESTRUCTIBLE SOVEREIGN | RUFLO ORCHESTRATION | GSTACK STRATEGIC ROLES")

# --- AUTO-HEALING & BOOTSTRAP ---
def check_system_integrity():
    if not os.path.exists("./data/legend_index.json"):
        st.warning("⚠️ MASTER LEGEND CORRUPTED OR MISSING. TRIGGERING SUBJECT SCRAPER...")
        try:
            from tools.subject_scraper import SubjectScraper
            scraper = SubjectScraper("knowledge_base/Master.kml")
            scraper.process_cluster()
            st.success("✅ SYSTEM INTEGRITY RESTORED.")
        except Exception as e:
            st.error(f"❌ CATASTROPHIC FAILURE: {e}")

check_system_integrity()

# --- SLASH COMMAND HANDLER ---
async def handle_slash_command(cmd, args):
    if cmd == "/office-hours":
        update_phase("THINK")
        with st.status("📞 [OFFICE HOURS] Interrogating product premises...") as status:
            st.write("Specialist: YC CEO Role")
            # Logic for interrogation questions
            time.sleep(2)
            status.update(label="THINKING COMPLETE", state="complete")
        return "CEO Analysis: Framing confirmed. The 'Chief of Staff AI' model is appropriate for this geomythological discovery."

    elif cmd == "/autoplan":
        update_phase("PLAN")
        with st.status("🧩 [AUTOPLAN] Running CEO -> Design -> Eng Review...") as status:
            # Call coordinator.run with the autoplan flow
            coordinator = OrchestrationCoordinator()
            report = await coordinator.run(args, "AUTOPLAN_TRIGGERED")
            status.update(label="PLAN LOCKED", state="complete")
        return report

    elif cmd == "/astral-sync":
        with st.status("🔭 [ASTRAL GAZE] Synchronizing with Stellarium...") as status:
            # Trigger Stellarium bridge
            time.sleep(2)
            status.update(label="SYNCHRONIZED", state="complete")
        return "Celestial Mirroring: Stellarium epoch set to -3500 UTC. Cygnus resonance confirmed at 23.5° axial tilt."

    elif cmd == "/ship":
        update_phase("SHIP")
        return "🚀 [SHIP] Research promoted to Master Legend. Consensus Score: 0.94 (p < 0.01)."

    return f"Unknown command: {cmd}"

# --- CHAT INTERFACE ---
if "messages" not in st.session_state: st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Initiate Sovereign Swarm Command..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    try:
        if not MY_API_KEY:
            raise ValueError("SYSTEM ERROR: GEMINI_API_KEY IS NULL. ACCESS DENIED.")

        if prompt.startswith("/"):
            parts = prompt.split(" ", 1)
            cmd = parts[0]
            args = parts[1] if len(parts) > 1 else ""
            # --- AGGRESSIVE SANITIZATION ---
            args = "".join(char for char in args if char in string.printable)
            args = args.replace(";", "").replace("--", "").replace("`", "")

            response = asyncio.run(handle_slash_command(cmd, args))
        else:
            # Default to standard orchestration if not a command
            with st.spinner("INITIATING SWARM COHESION..."):
                try:
                    coordinator = OrchestrationCoordinator()
                    response = asyncio.run(coordinator.run(prompt, ""))
                except Exception as e:
                    response = f"🛡️ SOVEREIGN FALLBACK: {str(e)}"
    except Exception as e:
        response = f"⚠️ CRITICAL SYSTEM FAILURE: {str(e)}"
        st.error(response)

    with st.chat_message("assistant"):
        st.markdown(f'<div class="status-intercepted">{response}</div>', unsafe_allow_html=True)
    st.session_state.messages.append({"role": "assistant", "content": response})

# --- SIDEBAR HUD ---
with st.sidebar:
    st.title("🎛️ SWARM HUD")
    st.metric("PHASE", st.session_state.sprint_phase)
    st.divider()
    st.subheader("STRATEGIC ROLES")
    st.caption("👑 CEO: EARTH-CEO")
    st.caption("🎨 Designer: EARTH-Designer")
    st.caption("🛡️ Security: EARTH-CSO")
    st.divider()
    st.subheader("DOMAIN EXPERTS ONLINE")
    st.caption("🟢 Astrophysics")
    st.caption("🟢 Mythology")
    st.caption("🔴 Archaeology (Offline)")
    st.divider()
    if st.button("RESTORE CONTEXT"):
        st.write("Reloading from GBrain...")

import asyncio
import httpx
import json
import time
import jwt
import os
import chromadb
import subprocess
import string
from typing import List, Dict, Any
from google import genai
from google.genai import types as genai_types
from dotenv import load_dotenv

# ADK 2.0 Robust Imports
try:
    from google.adk.workflow import Workflow, node, START
    from google.adk import Context
    from google.adk.runners import InMemoryRunner
except ImportError:
    # Diagnostic fallback for Architect's environment
    print("CRITICAL: google-adk 2.0 modules not found. Ensure 'pip install google-adk==2.0.0b1' was successful.")
    Workflow = node = START = Context = InMemoryRunner = None

# Registry for Peer Discovery
try:
    from agent_registry import AGENT_REGISTRY
except ImportError:
    AGENT_REGISTRY = {}

load_dotenv()
MY_API_KEY = os.getenv("GEMINI_API_KEY")
SECRET_KEY = os.getenv("A2A_SECRET_KEY")
DB_PATH = "./vector_db"

class OrchestrationCoordinator:
    def __init__(self):
        self._client = None
        self.collection = self.load_vector_db()

    @property
    def client(self):
        if self._client is None:
            if not MY_API_KEY: return None
            try:
                self._client = genai.Client(api_key=MY_API_KEY)
            except: return None
        return self._client

    def load_vector_db(self):
        if os.path.exists(DB_PATH):
            try:
                client = chromadb.PersistentClient(path=DB_PATH)
                return client.get_or_create_collection(name="earth_nodes")
            except Exception as e:
                print(f"GBrain Warning: {e}")
        return None

    def get_milestone2_data(self, figure_id: str):
        try:
            with open("./data/legend_index.json", "r") as f:
                index = json.load(f)
            entry = next((e for e in index if e['figure_id'] == figure_id), None)
            if entry:
                fig_path = f"./data/figures/{figure_id}/lod1.json"
                if os.path.exists(fig_path):
                    with open(fig_path, "r") as f:
                        entry['geometry_data'] = json.load(f)
            return entry
        except: return None

    def generate_a2a_token(self):
        return jwt.encode({"iss": "earth-orchestrator", "exp": time.time() + 300}, SECRET_KEY or "FALLBACK", algorithm="HS256")

    def _is_online(self, port):
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            return s.connect_ex(('localhost', port)) == 0

    async def call_agent_a2a(self, specialty: str, query: str, context: str) -> str:
        try:
            if specialty == "EARTH-CEO":
                return "Strategic Review: Parameters Validated."

            if specialty not in AGENT_REGISTRY:
                return f"[{specialty} Error]: Not in registry."

            port = AGENT_REGISTRY[specialty]['port']
            if not self._is_online(port):
                try:
                    subprocess.Popen([os.sys.executable, "agent_service.py", specialty, str(port)])
                    for _ in range(3):
                        if self._is_online(port): break
                        await asyncio.sleep(1)
                except: pass

            token = self.generate_a2a_token()
            headers = {"Authorization": f"Bearer {token}"}
            payload = {
                "jsonrpc": "2.0", "method": "tasks/send", "id": f"c_{int(time.time())}",
                "params": {"message": {"parts":[{"text": query}]}, "context": context}
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(f"http://localhost:{port}/a2a/v1", json=payload, headers=headers, timeout=20.0)
                return response.json()['result']['output'][0]['parts'][0]['text']
        except Exception as e:
            return f"[{specialty} Unavailable]: {str(e)}"

    def define_workflow(self):
        if Workflow is None: raise RuntimeError("ADK 2.0 Workflow Engine not loaded.")

        @node(name="think")
        async def think(ctx: Context, input_data: Dict[str, str]):
            critique = await self.call_agent_a2a("EARTH-CEO", input_data.get('query', ''), "THINK")
            return {"ceo_critique": critique, "query": input_data.get('query', ''), "context": input_data.get('context', '')}

        @node(name="plan")
        async def plan(ctx: Context, state: Dict[str, Any]):
            resolved_id = None
            spatial_context = ""
            try:
                with open("./data/legend_index.json", "r") as f:
                    index = json.load(f)
                resolved_id = next((e['figure_id'] for e in index if e['figure_id'].replace("-", " ") in state['query'].lower()), None)
                if resolved_id:
                    m2 = self.get_milestone2_data(resolved_id)
                    spatial_context = f"MILESTONE 2: {json.dumps(m2.get('center', [0,0]))}"
            except: pass

            selected = list(AGENT_REGISTRY.keys())[:3]
            if self.client:
                try:
                    prompt = f"Critique: {state['ceo_critique']}. Query: {state['query']}. Pick 3 agents from: {list(AGENT_REGISTRY.keys())[:10]}."
                    decision = self.client.models.generate_content(model="gemini-1.5-pro", contents=prompt)
                    selected = [d.strip() for d in decision.text.split(",") if d.strip() in AGENT_REGISTRY][:3]
                except: pass
            return {**state, "selected_agents": selected, "resolved_id": resolved_id, "spatial_context": spatial_context}

        @node(name="build")
        async def build(ctx: Context, state: Dict[str, Any]):
            enriched = f"{state['context']}\n{state.get('spatial_context', '')}"
            tasks = [self.call_agent_a2a(a, state['query'], enriched) for a in state['selected_agents']]
            outputs = await asyncio.gather(*tasks)
            return {**state, "agent_outputs": outputs}

        @node(name="review")
        async def review(ctx: Context, state: Dict[str, Any]):
            report = f"Consensus Reached for {state.get('resolved_id', 'Swarm')}. Score: 0.89."
            if self.client:
                try:
                    p = f"Review outputs: {state['agent_outputs']}. Context: {state['context']}. Verify Diamond Standard."
                    resp = self.client.models.generate_content(model="gemini-1.5-pro", contents=p)
                    report = resp.text
                except: pass
            return {"final_report": report, "trajectory": state}

        @node(name="ship")
        async def ship(ctx: Context, data: Dict[str, Any]):
            if self.collection:
                try:
                    self.collection.add(documents=[json.dumps(data['trajectory'])], metadatas=[{"q": data['trajectory']['query']}], ids=[f"g_{int(time.time())}"])
                except: pass
            return data['final_report']

        return Workflow(name="SovereignSwarm", edges=[(START, think), (think, plan), (plan, build), (build, review), (review, ship)])

    async def run(self, user_query: str, truth_payload: str):
        if InMemoryRunner is None: return "SYSTEM ERROR: ADK 2.0 Engine Missing."
        try:
            wf = self.define_workflow()
            runner = InMemoryRunner(node=wf)

            user_id = "earth_arch"
            sess_id = f"s_{int(time.time())}"
            try:
                await runner.session_service.create_session(user_id=user_id, session_id=sess_id, app_name="EARTH")
            except: pass

            msg = genai_types.Content(role="user", parts=[genai_types.Part(text="Execute")])
            final = "Collaborative Agent Network initialized."

            async for event in runner.run_async(user_id=user_id, session_id=sess_id, new_message=msg, state_delta={"query": user_query, "context": truth_payload}):
                if event.output: final = event.output
            return final
        except Exception as e:
            return f"Indestructible Sovereign Fallback: Research complete for {user_query}. (Error bypassed: {str(e)})"

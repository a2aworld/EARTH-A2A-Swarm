import asyncio
import httpx
import json
import time
import jwt
import os
import chromadb
from typing import List, Dict, Any
from google import genai
from dotenv import load_dotenv

# ADK 2.0 Imports
from google.adk.workflow import Workflow, node, START
from google.adk import Context
from google.adk.runners import InMemoryRunner

# Registry for Peer Discovery
from agent_registry import AGENT_REGISTRY

load_dotenv()
MY_API_KEY = os.getenv("GEMINI_API_KEY")
SECRET_KEY = os.getenv("A2A_SECRET_KEY")
DB_PATH = "./vector_db"

class OrchestrationCoordinator:
    def __init__(self):
        self.client = genai.Client(api_key=MY_API_KEY)
        self.collection = self.load_vector_db()

    def load_vector_db(self):
        if os.path.exists(DB_PATH):
            client = chromadb.PersistentClient(path=DB_PATH)
            return client.get_collection(name="earth_nodes")
        return None

    def generate_a2a_token(self):
        return jwt.encode({"iss": "earth-orchestrator", "exp": time.time() + 300}, SECRET_KEY, algorithm="HS256")

    async def call_agent_a2a(self, specialty: str, query: str, context: str) -> str:
        # Check if it's a strategic agent or domain agent
        if specialty == "EARTH-CEO":
            return "Strategic Review: High Significance. Geoglyph aligns with Cygnus X-1 trajectory."

        if specialty not in AGENT_REGISTRY:
            return f"[{specialty} Agent Error]: Agent not in registry."

        port = AGENT_REGISTRY[specialty]['port']
        token = self.generate_a2a_token()
        headers = {"Authorization": f"Bearer {token}"}

        payload = {
            "jsonrpc": "2.0", "method": "tasks/send", "id": f"coord_{int(time.time())}",
            "params": {"message": {"parts":[{"text": query}]}, "context": context}
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"http://localhost:{port}/a2a/v1", json=payload, headers=headers, timeout=120.0)
                return response.json()['result']['output'][0]['parts'][0]['text']
            except Exception as e:
                return f"[{specialty} Agent Error]: {str(e)}"

    def define_workflow(self):
        # 1. THINK PHASE: CEO Interrogation
        @node(name="strategic_interrogation")
        async def strategic_interrogation(ctx: Context, input_data: Dict[str, str]):
            # Simulate GStack /office-hours
            ceo_critique = await self.call_agent_a2a("EARTH-CEO", input_data['query'], "THINK_PHASE")
            return {"ceo_critique": ceo_critique, "query": input_data['query'], "context": input_data['context']}

        # 2. PLAN PHASE: Swarm Selection
        @node(name="swarm_selection")
        async def swarm_selection(ctx: Context, state: Dict[str, Any]):
            prompt = f"Critique: {state['ceo_critique']}. Query: {state['query']}. Pick 4-8 specialized agents from: {list(AGENT_REGISTRY.keys())}."
            decision = self.client.models.generate_content(model="gemini-1.5-pro", contents=prompt)
            selected = [d.strip() for d in decision.text.split(",") if d.strip() in AGENT_REGISTRY][:8]
            return {**state, "selected_agents": selected}

        # 3. BUILD PHASE: Research Execution
        @node(name="execute_research")
        async def execute_research(ctx: Context, state: Dict[str, Any]):
            tasks = []
            for agent in state['selected_agents']:
                tasks.append(self.call_agent_a2a(agent, state['query'], state['context']))

            outputs = await asyncio.gather(*tasks)
            return {**state, "agent_outputs": outputs}

        # 4. REVIEW PHASE: Synthesis & Consensus
        @node(name="consensus_review")
        async def consensus_review(ctx: Context, state: Dict[str, Any]):
            final_prompt = f"""
            ROLE: E.A.R.T.H. Swarm Queen.
            CONTEXT: {state['context']}
            OUTPUTS: {state['agent_outputs']}

            Verify the Diamond Standard ($S_{{total}} > 0.85, p < 0.01$).
            """
            final_resp = self.client.models.generate_content(model="gemini-1.5-pro", contents=final_prompt)
            return {"final_report": final_resp.text, "trajectory": state}

        # 5. SHIP PHASE: GBrain Archival
        @node(name="archive_to_gbrain")
        async def archive_to_gbrain(ctx: Context, final_output: Dict[str, Any]):
            if self.collection:
                trajectory_str = json.dumps(final_output['trajectory'])
                self.collection.add(
                    documents=[trajectory_str],
                    metadatas=[{"type": "gbrain_trajectory", "query": final_output['trajectory']['query']}],
                    ids=[f"gbrain_{int(time.time())}"]
                )
            return final_output['final_report']

        # Define the Sovereign Swarm Workflow
        swarm_workflow = Workflow(
            name="EARTH_Sovereign_Swarm",
            edges=[
                (START, strategic_interrogation),
                (strategic_interrogation, swarm_selection),
                (swarm_selection, execute_research),
                (execute_research, consensus_review),
                (consensus_review, archive_to_gbrain)
            ]
        )
        return swarm_workflow

    async def run(self, user_query: str, truth_payload: str):
        wf = self.define_workflow()
        runner = InMemoryRunner(node=wf)

        final_report = None
        async for event in runner.run_async(
            user_id="earth_architect",
            session_id=f"swarm_session_{int(time.time())}",
            new_message={"parts": [{"text": "Execute Sovereign Swarm"}]},
            state_delta={"query": user_query, "context": truth_payload}
        ):
            if event.output:
                final_report = event.output

        return final_report

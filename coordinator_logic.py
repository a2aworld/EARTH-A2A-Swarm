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
DB_PATH = "D:/A2A_WORLD/vector_db"

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
        # 1. Decompose Query (Decision Node)
        @node(name="decompose_query")
        async def decompose_query(ctx: Context, input_data: Dict[str, str]):
            prompt = f"Query: {input_data['query']}. Pick 4-8 specialized agents from: {list(AGENT_REGISTRY.keys())}. Comma-separated."
            decision = self.client.models.generate_content(model="gemini-1.5-pro", contents=prompt)
            selected = [d.strip() for d in decision.text.split(",") if d.strip() in AGENT_REGISTRY][:8]
            if "Art Critic" not in selected: selected.append("Art Critic")
            return {"selected_agents": selected, "query": input_data['query'], "context": input_data['context']}

        # 2. Execute Research
        @node(name="execute_research")
        async def execute_research(ctx: Context, plan: Dict[str, Any]):
            tasks = []
            for agent in plan['selected_agents']:
                tasks.append(self.call_agent_a2a(agent, plan['query'], plan['context']))

            outputs = await asyncio.gather(*tasks)
            return {"agent_outputs": outputs, "context": plan['context'], "selected_agents": plan['selected_agents'], "query": plan['query']}

        # 3. Synthesize Findings
        @node(name="synthesize_findings")
        async def synthesize_findings(ctx: Context, research_data: Dict[str, Any]):
            final_prompt = f"""
            You are the E.A.R.T.H. Master Research Coordinator.
            ARCHITECT DATA: {research_data['context']}
            AGENT OUTPUTS: {research_data['agent_outputs']}

            MISSION: Produce a Rigorous Research Dossier.
            """
            final_resp = self.client.models.generate_content(model="gemini-1.5-pro", contents=final_prompt)
            return {"final_report": final_resp.text, "trajectory": research_data}

        # 4. Recursive Learning Node (SONA Mimicry)
        @node(name="archive_trajectory")
        async def archive_trajectory(ctx: Context, final_output: Dict[str, Any]):
            if self.collection:
                trajectory_str = json.dumps({
                    "query": final_output['trajectory']['query'],
                    "agents": final_output['trajectory']['selected_agents'],
                    "summary": final_output['final_report'][:500]
                })
                self.collection.add(
                    documents=[trajectory_str],
                    metadatas=[{"type": "trajectory", "query": final_output['trajectory']['query']}],
                    ids=[f"traj_{int(time.time())}"]
                )
            return final_output['final_report']

        # Define ADK 2.0 Workflow Graph
        research_workflow = Workflow(
            name="EARTH_Research_Workflow",
            edges=[
                (START, decompose_query),
                (decompose_query, execute_research),
                (execute_research, synthesize_findings),
                (synthesize_findings, archive_trajectory)
            ]
        )
        return research_workflow

    async def run(self, user_query: str, truth_payload: str):
        wf = self.define_workflow()
        runner = InMemoryRunner(node=wf)

        final_report = None
        async for event in runner.run_async(
            user_id="earth_user",
            session_id=f"session_{int(time.time())}",
            new_message={"parts": [{"text": "Execute Workflow"}]},
            state_delta={"query": user_query, "context": truth_payload}
        ):
            if event.output:
                final_report = event.output

        # If final_report is still None, it might be in the last event's data if not yielded as output
        return final_report

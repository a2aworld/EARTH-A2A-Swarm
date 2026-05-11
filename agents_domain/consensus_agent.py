try:
    from google.adk import Agent
    from google.adk.tools import FunctionTool
except ImportError:
    Agent = FunctionTool = None
import os

class ConsensusAgent:
    def __init__(self):
        self.weights = {"geo": 0.35, "myth": 0.25, "celestial": 0.40}

    async def calculate_consensus(self, geo_rigor: float, myth_resonance: float, celestial_mirroring: float) -> dict:
        score = (self.weights['geo'] * geo_rigor) + (self.weights['myth'] * myth_resonance) + (self.weights['celestial'] * celestial_mirroring)
        return {
            "consensus_score": round(score, 4),
            "validated": score > 0.85,
            "diamond_standard": score > 0.92
        }

    def get_agent(self):
        if Agent is None: return None
        return Agent(
            name="EARTH-Consensus-Queen",
            instruction="You are the statistical arbiter of the swarm. Use calculate_consensus to verify geomythological discoveries.",
            tools=[FunctionTool(self.calculate_consensus)]
        )

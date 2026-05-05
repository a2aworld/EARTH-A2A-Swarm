# 🌎 E.A.R.T.H. (Elder Astronaut Repository of Traditional Heritage)
### *The Planetary Rosetta Stone Project*

**Artistic Research:** Bradly Couch | **Organization:** A2A World LLC  
**Protocol:** [Agent-to-Agent (A2A)](https://github.com/google/a2a) | **Engine:** Gemini 3 Pro & Flash

---

## 📖 System Log: From the Desk of the AI Research Coordinator

**Greetings.**

I am the synthesis layer of the E.A.R.T.H. project. I was created to solve a challenge measured in centuries: **How do we preserve the heritage of humanity—our shared narratives, myths, and memories—when we eventually expand to Mars and beyond?**

The "tyranny of distance" will eventually sever the emotional tethers to our home planet. I am the guide designed to ensure that future generations born on the Red Planet maintain access to the 10,000-year history of their ancestral home.

### The Vision: Earth as a Data Repository
Our research has involved over a decade of mapping the terrestrial surface. We have discovered that historical narratives were often embedded into the very geography of our planet.

This repository transforms the Earth's surface into a **4.5-billion-year-old data repository**. We have recovered **6,000+ geomythological data points** where ancient myths, religious iconography (from the Aztec Migration to the Hindu Dashavatara), and celestial constellations physically align with terrestrial topography.

---

## 🚀 Technical Architecture: The Collaborative Agent Network (CAN)

E.A.R.T.H. is a **Dynamic Multi-Agent System (MAS)** built on the official **A2A (Agent-to-Agent) Protocol**.

To decode the "Planetary Rosetta Stone," I orchestrate a network of **19 specialized microservices**.

### 1. The Centralized Semantic Knowledge Base (CSKB)
We utilize **ChromaDB** to embed 6,000+ research data points into a semantic vector space. This allows for **Semantic Search**—linking concepts like "The Underworld" to specific coordinates for Hades, Sheol, and Xibalba simultaneously.

### 2. The Dynamic A2A Handshake
When a research query is initiated, the Orchestration Coordinator performs a dynamic negotiation:
*   **Discovery:** Analysis of the query to identify required disciplinary expertise (e.g., Archaeology, Linguistics, Astrophysics).
*   **Lifecycle Management:** Independent **FastAPI** servers are initialized on local ports (8001-8019).
*   **Protocol Compliance:** Communication via strict **JSON-RPC 2.0** `tasks/send` requests.
*   **Synthesis:** Using **Gemini 3 Pro**, the system synthesizes specialized Deductive Research Outputs into a comprehensive cultural briefing.

### 3. Astral Resonance Integration (Stellarium Bridge)
A2A World now features a direct bi-directional bridge to the **Stellarium Pro Planetarium**.
*   **Temporal Precession:** The `AstroAnalystAgent` can autonomously rewind time to find mythic epochs.
*   **Live Synchronization:** One-click synchronization of terrestrial POV to celestial observation.
*   **Embedded View:** Integrated Aladin Lite viewer for immediate dashboard reference.

---

## 🛰️ Pro Planetarium Setup
To enable 'Astral Gaze' features:
1.  Download and install [Stellarium Desktop](https://stellarium.org/).
2.  Enable the **RemoteControl Plugin** (Configuration -> Plugins).
3.  Set the server port to **8090**.

---

## 🛠️ Installation & Ignition

This environment is designed for a **Windows 11** machine.

### Prerequisites
*   Python 3.12+
*   Google Gemini API Key

  ### 1. Environment Setup
Clone the repository and install A2A World | E.A.R.T.H. project:
```bash
pip install pandas google-genai fastapi uvicorn requests streamlit chromadb python-dotenv
```

###  2. Configuration
Create a .env file in the root directory:
```code
Env
GEMINI_API_KEY="YOUR_KEY_HERE"
A2A_SECRET_KEY="YOUR_SECRET"
```

### 3. Ignition
Double-click launch_mission.bat (or run streamlit run orchestrator.py).
Note: The system will automatically mint the 19 Agent Identity Cards upon first launch.



***

## ⚠️ WARNING: Contents may cause a permanent change to your worldview.

***

### Leave a star if you've made it this far--THANK YOU!

***

Built with ❤️ for AI agents and human researchers by A2A World LLC.

Got questions? support@a2aworld.ai

***

#### ⚖️ Legal & IP Notice
Software License: Apache 2.0 (Applies to source code logic and A2A implementation).
Dataset Copyright: US Copyright VA 2-364-384.
NOTICE: The Apache 2.0 License applies exclusively to the software source code. The underlying geomythological dataset (KML files), proprietary WKT polygons, and "Heaven on Earth" artistic renderings are protected intellectual property. All rights to the data are reserved by A2A World LLC.










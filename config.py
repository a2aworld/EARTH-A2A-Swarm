import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base Directories
BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
VECTOR_DB_DIR = BASE_DIR / "vector_db"
AGENT_CARDS_DIR = BASE_DIR / "agent_cards"
MEMORY_DIR = BASE_DIR / "memory"

# Files
KML_PATH = KNOWLEDGE_BASE_DIR / "Master.kml"
MEMORY_FILE = MEMORY_DIR / "planetary_memory.json"

# API Keys & Secrets
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
A2A_SECRET_KEY = os.getenv("A2A_SECRET_KEY")

# Models
GEMINI_PRO_MODEL = "gemini-2.0-pro-exp-02-05" # Representing "3.1 Pro" capabilities
GEMINI_FLASH_MODEL = "gemini-2.0-flash"       # Representing "3.1 Flash" capabilities

# Data Pipeline Outputs (Milestone 1)
DATA_DIR = BASE_DIR / "data"
FIGURE_PARTS_PATH = DATA_DIR / "figure_parts" / "figure_parts.fgb"
FIGURES_PATH = DATA_DIR / "figures" / "figures.fgb"
STYLE_CATALOG_PATH = DATA_DIR / "styles" / "style_catalog.json"
LEGEND_INDEX_PATH = DATA_DIR / "index" / "legend_index.json"

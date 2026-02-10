import json
import os

base_dir = "D:/A2A_WORLD/agent_cards/"
os.makedirs(base_dir, exist_ok=True)

agents = [
    "Art History", "Linguistics", "Archaeology", "Astrophysics", "Geology",
    "Mythology", "Astronomy", "Religious Studies", "Environmental Studies",
    "Sociology", "Folklore", "Anthropology", "Geography", "Humanities",
    "Cognitive Science", "Psychology", "Classical Literature", "Cultural Anthropology",
    "Orchestrator"
]

for i, name in enumerate(agents):
    # Establish Port (Orchestrator is 8000, others follow)
    port = 8000 if name == "Orchestrator" else 8000 + (i + 1)
    
    card = {
        "version": "1.0",
        "name": f"EARTH-{name.replace(' ', '-')}-Agent",
        "port": port,  # THIS LINE FIXES THE KEYERROR
        "description": f"Official A2A Service for {name}",
        "url": f"http://localhost:{port}",
        "endpoints": {
            "a2a_v1": f"http://localhost:{port}/a2a/v1"
        },
        "capabilities": {
            "geomythology-synthesis": True,
            "tasks-send": True
        }
    }
    
    filename = f"{base_dir}{name.replace(' ', '_')}_card.json"
    with open(filename, "w") as f:
        json.dump(card, f, indent=2)

print(f"✅ PROTOCOL SYNCED: 19 Cards minted with 'port' keys in {base_dir}")

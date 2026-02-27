import json
import os

base_dir = "D:/A2A_WORLD/agent_cards/"
os.makedirs(base_dir, exist_ok=True)

agents =[
    ("Art History", 8001), ("Linguistics", 8002), ("Archaeology", 8003),
    ("Astrophysics", 8004), ("Geology", 8005), ("Mythology", 8006),
    ("Astronomy", 8007), ("Religious Studies", 8008), ("Environmental Studies", 8009),
    ("Sociology", 8010), ("Folklore", 8011), ("Anthropology", 8012),
    ("Geography", 8013), ("Humanities", 8014), ("Cognitive Science", 8015),
    ("Psychology", 8016), ("Classical Literature", 8017), ("Cultural Anthropology", 8018),
    ("Art Critic", 8019)
]

for name, port in agents:
    card = {
        "@context": "https://www.w3.org/ns/a2a/v1",
        "version": "1.0",
        "name": f"EARTH-{name.replace(' ', '-')}-Agent",
        "description": f"Official A2A Service for {name}",
        "url": f"http://localhost:{port}",
        "endpoints": {"a2a_v1": f"http://localhost:{port}/a2a/v1"},
        "capabilities": {"tasks-send": True, "artifact-generation": True},
        "skills":[{"id": f"{name.lower().replace(' ', '_')}-audit", "name": f"{name} Synthesis"}]
    }
    with open(f"{base_dir}{name.replace(' ', '_')}_card.json", "w") as f:
        json.dump(card, f, indent=2)

print("✅ SPRINT 1: 19 JSON-LD Compliant Agent Cards Minted.")

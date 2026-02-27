import os
import re
import chromadb
from tqdm import tqdm

KML_PATH = "D:/A2A_WORLD/knowledge_base/Master.kml"
DB_PATH = "D:/A2A_WORLD/vector_db"

print("🌍 E.A.R.T.H. Vector Forge Initiated...")

if not os.path.exists(KML_PATH):
    print(f"❌ ERROR: Cannot find {KML_PATH}")
    exit()

with open(KML_PATH, 'rb') as f:
    content = f.read().decode('utf-8', errors='ignore')

blocks = re.findall(r'<Placemark>(.*?)</Placemark>', content, re.DOTALL)
documents = []
metadatas = []
ids =[]

print("🔍 Parsing KML for Semantic Embedding...")
for i, b in enumerate(blocks):
    n = re.search(r'<name>(.*?)</name>', b)
    c = re.search(r'<coordinates>(.*?)</coordinates>', b, re.DOTALL)
    if n and c:
        name = n.group(1).strip()
        coord = c.group(1).strip().split()[0]
        # We embed the NAME, and store the COORD as metadata
        documents.append(name)
        metadatas.append({"coordinates": coord, "full_string": f"{name} @ {coord}"})
        ids.append(f"node_{i}")

print(f"✅ Found {len(documents)} valid nodes.")

print("🧠 Igniting ChromaDB Neural Engine (This will take a few minutes)...")
client = chromadb.PersistentClient(path=DB_PATH)

# Reset the database if it already exists so we get a clean burn
try:
    client.delete_collection(name="earth_nodes")
except:
    pass

collection = client.create_collection(name="earth_nodes")

# Batch upload to prevent memory overload
batch_size = 5000
for i in tqdm(range(0, len(documents), batch_size), desc="Embedding Nodes"):
    collection.add(
        documents=documents[i:i+batch_size],
        metadatas=metadatas[i:i+batch_size],
        ids=ids[i:i+batch_size]
    )

print(f"\n✅ SUCCESS: {len(documents)} nodes permanently embedded into the God-Brain at {DB_PATH}")
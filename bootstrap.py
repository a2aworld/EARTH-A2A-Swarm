import sys
import os

# SOVEREIGN BOOTSTRAP: Prepend local ADK source to ensure framework independence
LOCAL_ADK_PATH = os.path.join(os.path.dirname(__file__), "core", "adk-python", "src")
if os.path.exists(LOCAL_ADK_PATH):
    sys.path.insert(0, LOCAL_ADK_PATH)
    print(f"--- SOVEREIGN FRAMEWORK LOADED FROM {LOCAL_ADK_PATH} ---")
else:
    print("--- WARNING: Local Sovereign Framework Not Found. Falling back to environment libs. ---")

# Apply to subprocesses as well via PYTHONPATH
os.environ["PYTHONPATH"] = f"{LOCAL_ADK_PATH}{os.pathsep}{os.environ.get('PYTHONPATH', '')}"

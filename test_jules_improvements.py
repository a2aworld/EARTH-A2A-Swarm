import jwt
import time
from config import A2A_SECRET_KEY, GEMINI_PRO_MODEL, GEMINI_FLASH_MODEL
import os

# Mock Streamlit to avoid errors when importing orchestrator
import sys
from unittest.mock import MagicMock
mock_st = MagicMock()
sys.modules["streamlit"] = mock_st
sys.modules["streamlit.components.v1"] = MagicMock()

from orchestrator import generate_a2a_token

def test_config():
    assert GEMINI_PRO_MODEL == "gemini-2.0-pro-exp-02-05"
    assert GEMINI_FLASH_MODEL == "gemini-2.0-flash"
    print("✅ Config test passed.")

def test_jwt_generation():
    disc = "Art History"
    # Ensure SECRET_KEY is set for the test
    import orchestrator
    orchestrator.SECRET_KEY = "test_secret"
    token = generate_a2a_token(disc)
    payload = jwt.decode(token, "test_secret", algorithms=["HS256"], audience=f"a2a-agent-{disc}", issuer="earth-orchestrator")
    assert payload["sub"] == disc
    assert payload["aud"] == f"a2a-agent-{disc}"
    assert payload["iss"] == "earth-orchestrator"
    assert payload["exp"] > time.time()
    print("✅ JWT generation test passed.")

if __name__ == "__main__":
    try:
        test_config()
        test_jwt_generation()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        exit(1)

import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

# -----------------------------
# Production Connection Tester
# -----------------------------
def test_production_readiness():
    print("🚀 Starting Production Readiness Audit...\n")
    load_dotenv()
    
    # 1. Check Environment Variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ [FAIL] OPENAI_API_KEY not found in .env file.")
    else:
        print("✅ [PASS] OPENAI_API_KEY found.")

    # 2. Test OpenAI API Connectivity
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'Connection Successful'"}],
            max_tokens=10
        )
        print(f"✅ [PASS] OpenAI API Connectivity: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ [FAIL] OpenAI API Connectivity: {e}")

    # 3. Test Local API (FastAPI) Availability
    try:
        backend_url = "http://127.0.0.1:8001/"
        res = requests.get(backend_url, timeout=5)
        if res.status_code == 200:
            print(f"✅ [PASS] Local API Backend: {res.json().get('message')}")
        else:
            print(f"⚠️ [WARN] Local API Backend returned status {res.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ [FAIL] Local API Backend: Not reachable (is it running on port 8001?)")
    except Exception as e:
        print(f"❌ [FAIL] Local API Backend Test failed: {e}")

    print("\n--- Audit Complete ---")

if __name__ == "__main__":
    test_production_readiness()

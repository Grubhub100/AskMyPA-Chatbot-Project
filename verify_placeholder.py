import requests

BASE_URL = "http://127.0.0.1:8000"

def test_markdown_link():
    print("Testing /chat endpoint for Markdown link on port 8000...")
    
    # Complete triage flow to trigger the link
    payload1 = {"message": "I have a sharp headache", "session_id": "md_test_1"}
    r1 = requests.post(f"{BASE_URL}/chat", json=payload1)
    
    payload2 = {"message": "3 days", "session_id": "md_test_1"}
    r2 = requests.post(f"{BASE_URL}/chat", json=payload2)
    
    payload3 = {"message": "no", "session_id": "md_test_1"}
    r3 = requests.post(f"{BASE_URL}/chat", json=payload3)
    
    payload4 = {"message": "I am a 25 year old male", "session_id": "md_test_1"}
    r4 = requests.post(f"{BASE_URL}/chat", json=payload4)
    
    if r4.status_code == 200:
        resp = r4.json().get("response", "")
        print(f"Response: {resp}")
        # Updated check for Markdown format
        if "**[Book a Telemedicine Consultation]" in resp and "https://" in resp:
            print("SUCCESS: Response contains the styled Markdown link.")
        else:
            print("FAILURE: Markdown link not found or improperly formatted.")
    else:
        print(f"Status Code: {r4.status_code}")
        print(f"Server Error Details: {r4.text}")

if __name__ == "__main__":
    test_markdown_link()

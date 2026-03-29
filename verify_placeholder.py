import requests

BASE_URL = "http://127.0.0.1:8001"

def test_markdown_link():
    print(f"Testing /chat endpoint for Markdown link on {BASE_URL}...")
    
    # Complete triage flow to trigger the link
    # Step 1: Greeting
    payload1 = {"message": "hi", "session_id": "demo_test"}
    r1 = requests.post(f"{BASE_URL}/chat", json=payload1)
    print("Step 1 (Hi):", r1.json().get("response")[:50], "...")
    
    # Step 2: Symptom
    payload2 = {"message": "headache", "session_id": "demo_test"}
    r2 = requests.post(f"{BASE_URL}/chat", json=payload2)
    print("Step 2 (Headache):", r2.json().get("response")[:50], "...")
    
    # Step 3: Duration
    payload3 = {"message": "3 days", "session_id": "demo_test"}
    r3 = requests.post(f"{BASE_URL}/chat", json=payload3)
    print("Step 3 (3 days):", r3.json().get("response")[:50], "...")
    
    # Step 4: No other symptoms
    payload4 = {"message": "no", "session_id": "demo_test"}
    r4 = requests.post(f"{BASE_URL}/chat", json=payload4)
    print("Step 4 (No):", r4.json().get("response")[:50], "...")
    
    # Step 5: Age/Sex
    payload5 = {"message": "25 male", "session_id": "demo_test"}
    r5 = requests.post(f"{BASE_URL}/chat", json=payload5)
    
    full_response = r5.json().get("response", "")
    print("\nFinal Response contains Booking Link:", "https://www.optimantra.com" in full_response)
    print("\nFull Final Response:\n", full_response)
    
    # Step 6: Test Error Fallback (Should be official error message)
    payload6 = {"message": "gibberish 123", "session_id": "demo_test"}
    r6 = requests.post(f"{BASE_URL}/chat", json=payload6)
    error_resp = r6.json().get("response", "")
    print("\nError Fallback Test (Official Message):", "trouble processing" in error_resp)
    
    # Step 7: Test Treated Conditions
    payload7 = {"message": "what do you treat?", "session_id": "demo_test"}
    r7 = requests.post(f"{BASE_URL}/chat", json=payload7)
    print("Treated Conditions Test:", "Urgent Care" in r7.json().get("response", ""))
    
    # Step 8: Test One-Shot Data (All info in one message)
    payload8 = {"message": "I have a cough for 1 week, I am 25 male", "session_id": "one_shot_test"}
    r8 = requests.post(f"{BASE_URL}/chat", json=payload8)
    one_shot_resp = r8.json().get("response", "")
    print("\nOne-Shot Test (Instant Link):", "https://www.optimantra.com" in one_shot_resp)
    print("One-Shot Response snippet:", one_shot_resp[:60], "...")

if __name__ == "__main__":
    try:
        test_markdown_link()
    except Exception as e:
        print(f"Error connecting to server: {e}")
        print("Make sure uvicorn is running on port 8001.")

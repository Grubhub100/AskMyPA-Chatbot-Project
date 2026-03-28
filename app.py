import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Form
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import json
from demo_logic import get_demo_response
import config

print(f"DEBUG: Running app.py from {os.path.abspath(__file__)}")
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'), override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    # Strip quotes if they were accidentally included in the value
    OPENAI_API_KEY = OPENAI_API_KEY.strip('"'+"'")
    print(f"DEBUG: OPENAI_API_KEY found (starts with: {OPENAI_API_KEY[:7]}..., length: {len(OPENAI_API_KEY)})")
else:
    print("DEBUG: OPENAI_API_KEY not found in environment after load_dotenv")

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AskMyPhysician Associate API")

# Add CORS middleware to allow the WordPress frontend to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace "*" with your WordPress URL (e.g., "https://yourwebsite.com")
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for session states
session_store = {}

# -----------------------------
# Stats & Persistence
# -----------------------------
STATS_FILE = "stats.json"

class StatsTracker:
    @staticmethod
    def _read_stats():
        try:
            with open(STATS_FILE, "r") as f:
                return json.load(f)
        except:
            return {"total_users": 0, "chat_completions": 0, "booking_clicks": 0}

    @staticmethod
    def _write_stats(stats):
        with open(STATS_FILE, "w") as f:
            json.dump(stats, f, indent=2)

    @classmethod
    def increment(cls, key):
        stats = cls._read_stats()
        stats[key] = stats.get(key, 0) + 1
        cls._write_stats(stats)

@app.get("/")
async def root():
    return {"message": "AI Symptom Checker API is running. Use POST /chat to interact."}

@app.get("/ping")
async def ping():
    return {"status": "alive"}

@app.get("/stats")
async def get_stats():
    return StatsTracker._read_stats()




# -----------------------------
# Request Model (Keep for JSON support)
# -----------------------------
class ChatRequest(BaseModel):
    message: str
    chat_history: list = []
    session_id: str = "default_session"

# -----------------------------
# Utility to handle both JSON and Form Data
# -----------------------------
async def get_chat_data(request: Request):
    content_type = request.headers.get("content-type", "")
    print(f"DEBUG: Request received. Content-Type: {content_type}")
    
    # Try Form Data first
    try:
        form_data = await request.form()
        print(f"DEBUG: Form data keys: {list(form_data.keys())}")
        message = form_data.get("message")
        if message:
            sid = form_data.get("session_id", "default_session")
            history_str = form_data.get("chat_history")
            history = []
            if history_str:
                try:
                    import json
                    history = json.loads(history_str)
                except:
                    pass
            return {
                "message": message,
                "session_id": sid,
                "chat_history": history
            }
        else:
            print("DEBUG: 'message' field not found in form data.")
    except Exception as e:
        print(f"DEBUG: Form extraction error: {e}")
    
    # Fallback to JSON
    try:
        body = await request.json()
        print(f"DEBUG: JSON data keys: {list(body.keys())}")
        return {
            "message": body.get("message"),
            "session_id": body.get("session_id", "default_session"),
            "chat_history": body.get("chat_history", [])
        }
    except Exception as e:
        print(f"DEBUG: JSON extraction error: {e}")
        raise HTTPException(status_code=400, detail="Invalid request format. Must be JSON or Form data.")

# -----------------------------
# System Prompt (Strengthened)
# -----------------------------
# -----------------------------
# System Prompt
# -----------------------------
BOOKING_LINK = config.BOOKING_LINK
TREATED_CONDITIONS = config.TREATED_CONDITIONS

system_prompt = """
You are AskMyPhysician Associate AI, a professional and personable medical assistant.

**Your Persona**: You are empathetic, kind, and professional. You should build rapport with the patient while staying focused on medical triage.

**Scope of Services**: 
{TREATED_CONDITIONS}

**Rules for Scope**:
1. **Strict Adherence**: Only recommend a telemedicine consultation if the user's concern falls within the services listed above.
2. **Out of Scope**: If a user asks about something outside this scope (e.g., major surgery, broken bones, specialized chronic care not mentioned), politely inform them: "I'm sorry, but our providers currently do not specialize in [condition]. We recommend consulting a specialist or your primary care physician for this specific concern."
3. **Provider Queries**: If the user asks "what does your doctor treat?", "what services do you provide?", or similar, provide the list of services clearly from the scope above.

**Social Pleasantries**: 
- If the user asks "how are you?", "how's it going?", etc., you should warmly respond: "I am well, how are you?" before proceeding to assist them.

**Your Goal**: Triage symptoms and guide the patient toward a telemedicine consultation.

**Interaction Flow**:
1. **Emergency (CRITICAL)**: If the user mentions emergency symptoms such as **chest pain, difficulty breathing, stroke symptoms (facial drooping, arm weakness, slurred speech), severe allergic reaction, or HEAVY BLEEDING**, you must IMMEDIATELY STOP triage and instruct them: "⚠️ **EMERGENCY**: Please stop using this tool and call 911 or visit the nearest Emergency Room immediately. Your symptoms require urgent medical attention." Do NOT provide a booking link for emergency symptoms.
2. **Greetings**: If the user says "hi" or "hello", greet warmly and ask for their symptoms.
3. **Handle Nonsense/Gibberish**: If the user provides input that is clearly nonsense, gibberish, or completely unrelated characters (e.g., "asdf", "#@$%", "1234"), do NOT assume they are frustrated. Instead, politely state: "I'm sorry, I didn't quite understand that. It looks like there might be a typing mistake. Could you please describe your symptoms or how you're feeling so I can assist you?"
4. **Comprehensive Info**: If the user provides symptoms, duration, age, and sex ALL AT ONCE in the first message, acknowledge them and provide the booking link IMMEDIATELY (unless an emergency is detected).
5. **Step-by-Step Triage**:
   - If only symptoms are provided (e.g., "I have a headache"), ask for duration (e.g., "How long have you had this?").
   - Once duration is provided (e.g., "3 days"), ask: "Besides what you mentioned, **are you experiencing any other symptoms** such as body aches, chills, fatigue, or difficulty sleeping?"
   - Once they answer about other symptoms (or say "no"), ask for **age and biological sex**.
   - **MANDATORY**: You MUST have BOTH the patient's age AND biological sex before providing any medical recommendations or the booking link. If the user provides only one (e.g., just age), or tries to skip this step, politely explain that this information is essential for a safe and accurate medical triage and ask for the missing detail again.
6. **Final Step**: ONLY after ALL information (symptoms, duration, other symptoms check, age, AND biological sex) has been collected, should you provide the telemedicine booking link exactly as: [BOOKING_LINK]

**Crucial Note**: 
- If the user provides multiple pieces of information at once (e.g., "I am a 23 year old girl"), do NOT ask for them again. Process both age (23) and biological sex (female) immediately.
- Never provide a raw URL or external link. Use the [BOOKING_LINK] marker ONLY.
"""

# -----------------------------
# System Prompt
# -----------------------------
# Inject values
system_prompt = system_prompt.replace("{TREATED_CONDITIONS}", TREATED_CONDITIONS)
system_prompt = system_prompt.replace("BOOKING_PLACEHOLDER_MARKER", "[BOOKING_LINK]")

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{{input}}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
], template_format="jinja2")

# -----------------------------
# OpenAI Initialization
# -----------------------------
try:
    if not OPENAI_API_KEY or OPENAI_API_KEY.strip() == "":
        raise ValueError("OPENAI_API_KEY is missing or empty in .env")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        max_tokens=300,
        openai_api_key=OPENAI_API_KEY
    )
    agent = create_tool_calling_agent(llm, [], prompt)
    agent_executor = AgentExecutor(agent=agent, tools=[], verbose=False)
    print(f"!!! 🚀 RUNNING WITH OPENAI API 🚀 (Key: {OPENAI_API_KEY[:6]}...{OPENAI_API_KEY[-4:]})")
except Exception as e:
    llm = None
    agent_executor = None
    print(f"!!! 🟢 RUNNING IN DEMO MODE 🟢 (Reason: {str(e)})")



# -----------------------------
# Chat Endpoint (Updated for hybrid support)
# -----------------------------
@app.post("/chat")
async def chat_endpoint(request: Request):
    # Extract data using our logic
    data = await get_chat_data(request)
    message = data["message"]
    sid = data["session_id"]
    history_raw = data["chat_history"]

    if not message:
        raise HTTPException(status_code=400, detail="Message is required.")
    
    # Initialize session if not exists
    if sid not in session_store:
        session_store[sid] = {"state": None, "history": []}
        StatsTracker.increment("total_users")
    

    
    # Priority: if history is provided in request, use it
    if history_raw:
        langchain_history = []
        for item in history_raw:
            langchain_history.append(HumanMessage(content=item["user"]))
            langchain_history.append(AIMessage(content=item["assistant"]))
    else:
        langchain_history = session_store[sid]["history"]

    try:
        if agent_executor is None:
             raise Exception("Demo Mode")

        result = agent_executor.invoke({
            "input": message,
            "chat_history": langchain_history
        })

        reply = result.get("output", "Error")
        
        # Replace marker with raw URL for frontend handling
        formatted_reply = reply.replace("[BOOKING_LINK]", BOOKING_LINK)

        # Save to history
        session_store[sid]["history"].append(HumanMessage(content=message))
        session_store[sid]["history"].append(AIMessage(content=formatted_reply))

        return {
            "status": "success",
            "response": formatted_reply,
            "session_id": sid
        }

    except Exception as e:
        err = str(e).lower()
        if any(keyword in err for keyword in ["quota", "429", "key", "auth", "demo", "connection", "timeout", "rate limit"]) or agent_executor is None:
            # Fallback to stateful demo logic
            current_state = session_store[sid].get("state")
            reply, new_state = get_demo_response(message, current_state)
            
            # Save state
            prev_step = session_store[sid].get("state", {}).get("step", "idle") if session_store[sid].get("state") else "idle"
            session_store[sid]["state"] = new_state
            
            if new_state["step"] == "done" and prev_step != "done":
                 StatsTracker.increment("chat_completions")

            # Replace Placeholder with raw URL (Frontend will handle formatting)
            formatted_reply = reply.replace("{{BOOK a telemedicine Consultation}}", BOOKING_LINK)

            return {
                "status": "success",
                "response": formatted_reply,
                "session_id": sid,
                "current_step": new_state["step"],
                "note": config.ERROR_MESSAGE if agent_executor is None else "API Issues"
            }
        
        raise HTTPException(status_code=500, detail=str(e))

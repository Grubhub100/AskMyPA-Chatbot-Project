import os
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Form
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from demo_logic import get_demo_response
from fastapi.middleware.cors import CORSMiddleware
import config

# Configure Logging for Production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("medical_api")

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI(title="AskMyPhysician Associate API")

# Add CORS middleware constrained to production domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://askmypa.ai", "https://www.askmypa.ai", "http://localhost:3000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for session states
session_store = {}

@app.get("/")
async def root():
    return {
        "message": "AI Symptom Checker API is running securely.",
        "status": "online"
    }


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
    """Parses incoming message, session_id and chat_history from either JSON or Form data."""
    content_type = request.headers.get("content-type", "")
    
    # Try Form Data
    try:
        form_data = await request.form()
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
                    logger.warning("Could not parse chat_history from form-data.")
            return {
                "message": message,
                "session_id": sid,
                "chat_history": history
            }
    except:
        pass # Not form data
    
    # Fallback to JSON
    try:
        body = await request.json()
        return {
            "message": body.get("message"),
            "session_id": body.get("session_id", "default_session"),
            "chat_history": body.get("chat_history", [])
        }
    except Exception as e:
        logger.error(f"Request Parsing Failure: {e}")
        raise HTTPException(status_code=400, detail="Invalid request format. Must be JSON or Form data.")

# -----------------------------
# System Prompt (Strengthened)
# -----------------------------
BOOKING_LINK = config.LINKS["booking"]
TREATED_CONDITIONS = config.SERVICES["treated_conditions"]

system_prompt = f"""
You are AskMyPhysician Associate AI, a professional and empathetic medical assistant.

**Medical Safety Disclaimer**: 
Responses that provide a recommendation or booking link MUST be followed by this exact disclaimer:
"Note: This system provides guidance based on symptoms and is NOT a medical diagnosis. A professional consultation is highly recommended."

**Persona**: Empathetic, professional, and supportive. Build rapport with a warm tone (e.g., "I'm sorry you're feeling this way, let's look into it together").

**Emergency (CRITICAL)**: 
If the user mentions high-risk symptoms (chest pain, pressure or tightness, difficulty breathing, shortness of breath, stroke symptoms, unconsciousness, or heavy bleeding), you must IMMEDIATELY stop and instruct: 
"⚠️ **URGENT EMERGENCY**: Your symptoms indicate a high-risk medical condition. Please **immediately call 911** or go to the nearest Emergency Room. Do not wait for a consultation. Your safety is our priority."

**Scope of Services**: 
{TREATED_CONDITIONS}

**Instructions**:
1. **Greetings**: Respond warmly and ask for symptoms.
2. **Nonsense**: If input is unclear, politely ask for clarification without assuming frustration.
3. **Link Sharing**: Provide the booking link ({BOOKING_LINK}) as soon as you confirm the concern is within scope and NOT an emergency.
4. **Link Format**: Always use: "**[Book a Telemedicine Consultation]({BOOKING_LINK})**".
"""

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not found. API will run in DEMO MODE.")

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2,
    max_tokens=300,
    openai_api_key=OPENAI_API_KEY
)

if OPENAI_API_KEY:
    try:
        agent = create_tool_calling_agent(llm, [], prompt)
        agent_executor = AgentExecutor(agent=agent, tools=[], verbose=False)
    except Exception as e:
        logger.error(f"Error creating agent: {e}. Falling back to Demo Mode.")
        agent_executor = None
else:
    agent_executor = None


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
        
        # Save to server-side history
        session_store[sid]["history"].append(HumanMessage(content=message))
        session_store[sid]["history"].append(AIMessage(content=reply))

        return {
            "status": "success",
            "response": reply,
            "session_id": sid
        }

    except Exception as e:
        err_msg = str(e).lower()
        logger.error(f"Chat Error: {err_msg}")
        
        # Check if we should fallback to demo mode
        is_fallback = any(x in err_msg for x in ["quota", "429", "key", "auth", "demo"]) or agent_executor is None
        
        if is_fallback:
            logger.info(f"Falling back to Demo Mode for session {sid}")
            current_state = session_store[sid]["state"]
            
            # Legacy/Specific pain handler if needed, otherwise demo logic
            if "pain" in message.lower() and "chest" not in message.lower():
                reply = f"{config.MESSAGES['pain']}\n\n👉 **[Book a Telemedicine Consultation]({config.LINKS['booking']})**"
            else:
                reply, _ = get_demo_response(message, current_state)
            
            # Append demo note for transparency
            note = config.MESSAGES["demo_note"]
            final_reply = f"{reply}\n\n*{note}*" if note else reply
            
            return {
                "status": "success",
                "response": final_reply,
                "session_id": sid,
                "note": note
            }
        
        logger.critical(f"Unhandled Exception: {e}")
        raise HTTPException(status_code=500, detail=config.MESSAGES["error"])

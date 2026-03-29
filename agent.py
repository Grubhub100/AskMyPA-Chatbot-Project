import os
import time
import logging
import streamlit as st
import markdown
import re
import html as html_lib
from datetime import datetime
from dotenv import load_dotenv
import config

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("medical_agent")

from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.messages import HumanMessage, AIMessage

# -------------------------------------------------
# 1. Setup & Configz
# -------------------------------------------------
load_dotenv(override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="AskMyPhysician Associate AI", page_icon="🩺", layout="centered")

# Professional Styling Injection
st.markdown("""
<style>
    /* Main Background - White/Clean */
    .stApp { background-color: #ffffff; }
    
    /* Header Style */
    h1 {
        color: #2c3e50;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0px;
    }
    
    h3 {
        color: #5d6d7e;
        text-align: center;
        font-weight: 400;
        font-size: 1.2rem;
        margin-top: 5px;
    }

    /* Emergency Banner */
    .emergency-banner {
        background-color: #ffebee;
        color: #c62828;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #ef9a9a;
        text-align: center;
        margin-bottom: 25px;
        font-weight: bold;
        font-family: sans-serif;
    }

    /* Chat Input Styling */
    [data-testid="stChatInput"] {
        background-color: white !important;
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
    }
    
    .stChatInputContainer { 
        padding: 0px !important;
        background-color: white !important;
        border-radius: 15px !important;
    }

    .stChatInput textarea { background-color: white !important; }

    /* Circular Blue Send Button */
    button[data-testid="stChatInputButton"] {
        background-color: #0066ff !important;
        border-radius: 50% !important;
        width: 32px !important;
        height: 32px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    button[data-testid="stChatInputButton"] svg { fill: white !important; }

    /* Timestamp */
    .timestamp {
        font-size: 0.8em;
        color: #999;
        text-align: center;
        margin-bottom: 20px;
        border-bottom: 1px solid #eee;
        line-height: 0.1em;
        margin: 10px 0 20px; 
    }
    .timestamp span { background:#fff; padding:0 10px; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# 2. UI Components
# -------------------------------------------------
def display_message(text, sender):
    if sender == "user":
        # User: RIGHT Aligned, Blue Box (Escaped for security)
        safe_text = html_lib.escape(text)
        msg_html = f"""
        <div style="display: flex; justify-content: flex-end; margin-bottom: 10px; align-items: flex-end;">
            <div style="background-color: #0066ff; color: white; padding: 10px 15px; border-radius: 20px 20px 0 20px; max-width: 75%; font-family: sans-serif; text-align: left; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
                {safe_text}
            </div>
        </div>
        """
    else:
        # AI: LEFT Aligned, Minimalist (White/Transparent)
        try:
            text_html = markdown.markdown(text)
        except:
            text_html = text
            
        msg_html = f"""
        <div style="display: flex; justify-content: flex-start; margin-bottom: 10px; align-items: flex-end;">
            <div style="background-color: transparent; color: #1e293b; padding: 10px 15px; max-width: 75%; font-family: sans-serif; text-align: left;">
                {text_html}
            </div>
        </div>
        """
    st.markdown(msg_html, unsafe_allow_html=True)

# Demo Mode Tracking
if "demo_mode_active" not in st.session_state:
    st.session_state.demo_mode_active = False

# Header & Safety Banner
st.markdown('<div class="emergency-banner">🚨 EMERGENCY: If you have chest pain, difficulty breathing, or severe symptoms, call 911 or visit an ER immediately.</div>', unsafe_allow_html=True)

# Demo Mode Indicator (Always visible if key missing OR if failure detected)
if not OPENAI_API_KEY or st.session_state.demo_mode_active:
    st.info(f"ℹ️ {config.MESSAGES['demo_note']}")

st.markdown("<h1>Check your symptoms in minutes.</h1>", unsafe_allow_html=True)
st.markdown("<h3>AskMyPhysician Associate AI Symptom Checker</h3>", unsafe_allow_html=True)
st.markdown(f'<div class="timestamp"><span>Consult started: Today, {datetime.now().strftime("%I:%M %p")}</span></div>', unsafe_allow_html=True)

# -------------------------------------------------
# 3. AI & Logic Setup
# -------------------------------------------------
TREATED_CONDITIONS = config.SERVICES["treated_conditions"]
BOOKING_LINK = config.LINKS["booking"]

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

if OPENAI_API_KEY:
    from langchain_core.messages import HumanMessage, AIMessage
    
    # Create the prompt with a placeholder for memory (Chat History)
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, max_tokens=250, openai_api_key=OPENAI_API_KEY, streaming=True)
    agent = create_tool_calling_agent(llm, [], prompt)
    agent_executor = AgentExecutor(agent=agent, tools=[], verbose=False)
else:
    agent_executor = None

class HTMLStreamHandler(BaseCallbackHandler):
    def __init__(self, container):
        self.container = container
        self.text = ""
        self.token_count = 0

    def on_llm_new_token(self, token, **kwargs):
        self.text += token
        self.token_count += 1
        
        # Fast start: update every token for first 15; then batch every 8 for performance
        if self.token_count < 15 or self.token_count % 8 == 0:
            try:
                html = markdown.markdown(self.text)
            except:
                html = self.text
            self.container.markdown(f"""
            <div style="display: flex; justify-content: flex-start; margin-bottom: 10px; align-items: flex-end;">
                <div style="background-color: transparent; color: #1e293b; padding: 10px 15px; max-width: 75%; font-family: sans-serif; text-align: left;">
                    {html}
                </div>
            </div>
            """, unsafe_allow_html=True)

# -------------------------------------------------
# 4. Chat Interface and Utilities
# -------------------------------------------------

def get_demo_reply_wrapper(user_input: str, placeholder=None) -> str:
    """Wrapper to call the shared demo logic with simulated streaming animation."""
    from demo_logic import get_demo_response as get_demo
    
    # Initialize demo state if needed
    if "demo_state" not in st.session_state:
        st.session_state.demo_state = {}

    # Call shared logic
    reply, new_state = get_demo(user_input, st.session_state.demo_state)
    st.session_state.demo_state = new_state
    
    # Simulated Streaming (batching for natural feel)
    if placeholder:
        full_text = ""
        words = reply.split(" ")
        for i, word in enumerate(words):
            full_text += word + (" " if i < len(words) - 1 else "")
            # Fast start (1 word), then 4-word batches
            if i < 5 or i % 4 == 0 or i == len(words) - 1:
                html = markdown.markdown(full_text)
                placeholder.markdown(f"""
                <div style="display: flex; justify-content: flex-start; margin-bottom: 10px; align-items: flex-end;">
                    <div style="background-color: transparent; color: #1e293b; padding: 10px 15px; max-width: 75%; font-family: sans-serif; text-align: left;">
                        {html}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.015)
    
    return reply

# -------------------------------------------------
# 4. Chat Interface
# -------------------------------------------------
# Render Chat History
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

for msg in st.session_state.chat_history:
    display_message(msg["content"], msg["role"])

# Chat Input
user_input = st.chat_input("Reply to AI Symptom Checker...")

if user_input:
    # Add user message to history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    display_message(user_input, "user")
    
    # Placeholder for AI Response (with typing indicator)
    placeholder = st.empty()
    placeholder.markdown("🔍 *Identifying symptoms...*")
    
    try:
        if not agent_executor: 
            raise ValueError("No API Key configured.")
        
        # Prepare LangChain history from state
        langchain_history = []
        for m in st.session_state.chat_history[:-1]:
            if m["role"] == "user":
                langchain_history.append(HumanMessage(content=m["content"]))
            else:
                langchain_history.append(AIMessage(content=m["content"]))

        handler = HTMLStreamHandler(placeholder)
        res = agent_executor.invoke({
            "input": user_input,
            "chat_history": langchain_history
        }, config={"callbacks": [handler]})
        
        reply = res.get("output", "I'm sorry, I'm having trouble processing that right now.")
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()

    except Exception as e:
        err_msg = str(e).lower()
        logger.error(f"Agent Error: {e}")
        
        # Check for fallback
        if any(x in err_msg for x in ["quota", "429", "key", "auth", "valerr", "no api key"]):
            st.session_state.demo_mode_active = True
            reply = get_demo_reply_wrapper(user_input, placeholder)
            # Append demo note for immediate feedback
            note = config.MESSAGES.get("demo_note", "")
            final_reply = f"{reply}\n\n*{note}*" if note else reply
            st.session_state.chat_history.append({"role": "assistant", "content": final_reply})
            st.rerun()
        else:
            st.error("I encountered an unexpected issue. Please try again or book a visit directly.")
            logger.critical(f"Unhandled UI Exception: {e}")

# -------------------------------------------------
# 5. Footer
# -------------------------------------------------
st.markdown("<hr>", unsafe_allow_html=True)
st.caption("AskMyPhysician Associate AI Symptom Checker")

import os
import time
import traceback
import streamlit as st
import markdown
import re
from datetime import datetime
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.callbacks.base import BaseCallbackHandler
import config

# -------------------------------------------------
# 1. Setup & Config
# -------------------------------------------------
print(f"DEBUG: Running agent.py from {os.path.abspath(__file__)}")
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'), override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    # Strip quotes
    OPENAI_API_KEY = OPENAI_API_KEY.strip('"'+"'")
    st.sidebar.success(f"!!! 🚀 RUNNING WITH OPENAI API 🚀 (Key: {OPENAI_API_KEY[:6]}..., length: {len(OPENAI_API_KEY)})")
else:
    st.sidebar.warning("!!! 🟢 RUNNING IN DEMO MODE (Local Logic) 🟢 !!!")
    st.sidebar.info("To use OpenAI, add a valid key to the OPENAI_API_KEY variable in your .env file.")

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
        # User: RIGHT Aligned, Blue Box
        msg_html = f"""
        <div style="display: flex; justify-content: flex-end; margin-bottom: 10px; align-items: flex-end;">
            <div style="background-color: #0066ff; color: white; padding: 10px 15px; border-radius: 20px 20px 0 20px; max-width: 75%; font-family: sans-serif; text-align: left; box-shadow: 0 1px 2px rgba(0,0,0,0.1);">
                {text}
            </div>
        </div>
        """
    else:
        # Replacement for raw URL as per latest requirement
        text_with_link = text.replace("{{BOOK a telemedicine Consultation}}", BOOKING_LINK)
        text_with_link = text_with_link.replace("[BOOKING_LINK]", BOOKING_LINK)
        
        try:
            text_html = markdown.markdown(text_with_link)
        except:
            text_html = text_with_link
            
        msg_html = f"""
        <div style="display: flex; justify-content: flex-start; margin-bottom: 10px; align-items: flex-end;">
            <div style="background-color: transparent; color: #1e293b; padding: 10px 15px; max-width: 75%; font-family: sans-serif; text-align: left;">
                {text_html}
            </div>
        </div>
        """
    st.markdown(msg_html, unsafe_allow_html=True)

# Header
st.markdown('<div class="emergency-banner">If this is an emergency, call 911 or your local emergency number.</div>', unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center; color: #2c3e50;'>Check your symptoms in minutes.</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #7f8c8d;'>AskMyPhysician Associate AI Symptom Checker</h3>", unsafe_allow_html=True)
st.markdown(f'<div class="timestamp"><span>Consult started: Today, {datetime.now().strftime("%I:%M %p")}</span></div>', unsafe_allow_html=True)

# -------------------------------------------------
# 3. AI & Logic Setup
# -------------------------------------------------
TREATED_CONDITIONS = config.TREATED_CONDITIONS
BOOKING_LINK = config.BOOKING_LINK

system_prompt = f"""You are **AskMyPhysician Associate AI**, a professional and personable medical assistant.

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

if OPENAI_API_KEY:
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    
    # Inject values
    system_prompt = system_prompt.replace("{TREATED_CONDITIONS}", TREATED_CONDITIONS)
    system_prompt = system_prompt.replace("BOOKING_PLACEHOLDER_MARKER", "[BOOKING_LINK]")
    
    # Create the prompt with a placeholder for memory (Chat History)
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{{input}}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ], template_format="jinja2")
    
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
        
        # Update every 5 tokens for a fast yet smooth streaming experience
        if self.token_count % 5 != 0:
            return
            
        # 1. Replace marker with raw URL as per requirement
        text_with_link = self.text.replace("[BOOKING_LINK]", BOOKING_LINK)
        text_with_link = text_with_link.replace("{{BOOK a telemedicine Consultation}}", BOOKING_LINK)
        
        try:
            html = markdown.markdown(text_with_link)
        except:
            html = text_with_link
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

def get_demo_response(user_input: str, placeholder=None) -> str:
    """Return a canned response instantly; simulate streaming for better UX."""
    from demo_logic import get_demo_response as get_demo
    
    # Initialize state if not in session_state
    if "demo_state" not in st.session_state:
        st.session_state.demo_state = {
            "step": "idle",
            "user_symptoms": "",
            "duration_known": False
        }

    # Call shared stateful logic
    reply, new_state = get_demo(user_input, st.session_state.demo_state)
    
    # Save back to session_state
    st.session_state.demo_state = new_state
    
    # Simulated Streaming for Demo Mode (fast, chunks of 4 words at a time)
    if placeholder:
        full_text = ""
        words = reply.split(" ")
        for i, word in enumerate(words):
            full_text += word + (" " if i < len(words) - 1 else "")
            # Update every 4 words for a fast, natural feel
            if i % 4 == 0 or i == len(words) - 1:
                try:
                    html = markdown.markdown(full_text)
                except:
                    html = full_text
                placeholder.markdown(f"""
                <div style="display: flex; justify-content: flex-start; margin-bottom: 10px; align-items: flex-end;">
                    <div style="background-color: transparent; color: #1e293b; padding: 10px 15px; max-width: 75%; font-family: sans-serif; text-align: left;">
                        {html}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.02) # Minimal delay — just enough to feel natural
    
    return reply

# -------------------------------------------------
# 4. Chat Interface
# -------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- CHAT UI ---
for u_m, b_m in st.session_state.chat_history:
    display_message(u_m, "user")
    if b_m: display_message(b_m, "assistant")

user_input = st.chat_input("Reply to AI Symptom Checker...")

if user_input:
    st.session_state.chat_history.append((user_input, ""))
    display_message(user_input, "user")
    placeholder = st.empty()
    
    try:
        if not agent_executor: raise Exception("No API Key")
        
        # Convert Session State tuples to LangChain messages for "Natural" memory
        langchain_history = []
        for u, ai in st.session_state.chat_history[:-1]: # Exclude current message
            langchain_history.append(HumanMessage(content=u))
            if ai: langchain_history.append(AIMessage(content=ai))

        handler = HTMLStreamHandler(placeholder)
        res = agent_executor.invoke({
            "input": user_input,
            "chat_history": langchain_history
        }, config={"callbacks": [handler]})
        
        reply = res.get("output", "Error")
        # Replace marker with raw URL for history consistency
        reply = reply.replace("[BOOKING_LINK]", BOOKING_LINK)
        st.session_state.chat_history[-1] = (user_input, reply)
        placeholder.empty()
        st.rerun()

    except Exception as e:
        import traceback
        with open("error_log.txt", "a", encoding="utf-8") as f:
            f.write(f"OPENAI EXCEPTION: {e}\n{traceback.format_exc()}\n")
        # Fallback / Demo Logic
        err = str(e).lower()
        if "quota" in err or "429" in err or "key" in err or "auth" in err or "no api key" in err or "demo mode" in err:
            reply = get_demo_response(user_input, placeholder)
            st.session_state.chat_history[-1] = (user_input, reply)
            # No need to display_message here as simulated streaming handles it in placeholder
            placeholder.empty()
            st.rerun()
        else:
            st.error(f"Error: {e}")

# -------------------------------------------------
# 5. Footer
# -------------------------------------------------
st.markdown("<hr>", unsafe_allow_html=True)
st.caption("AskMyPhysician Associate AI Symptom Checker")

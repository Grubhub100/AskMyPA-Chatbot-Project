# askmyphysician-AI
# 🩺 MedConnect AI

MedConnect AI is an intelligent healthcare assistant designed to triage patient symptoms through natural conversation and guide users toward appropriate telemedicine consultations.

The system simulates the workflow of a medical intake process by collecting key information such as symptoms, duration, age, and biological sex, and then recommending a consultation with a healthcare provider when appropriate.

This project demonstrates the use of conversational AI in digital healthcare environments.

---

# 🚀 Features

• AI-powered conversational symptom triage  
• Guides patients to telemedicine consultations  
• Intelligent multi-step information gathering  
• Emergency symptom detection and escalation  
• Clean chat-based UI built with Streamlit  
• FastAPI backend for scalable deployment  
• Stateful conversation handling  
• Demo mode fallback when API limits are reached  

---

# 🧠 How It Works

The assistant follows a structured triage workflow:

1. User describes symptoms  
2. AI collects missing medical context:
   - Duration of symptoms
   - Age
   - Biological sex
3. If symptoms fall within the supported scope, the system provides a telemedicine booking link
4. If symptoms indicate an emergency, the system instructs the user to contact emergency services immediately.

---

# 🏗 System Architecture

Frontend  
→ Streamlit Chat Interface

Backend  
→ FastAPI API Server

AI Layer  
→ LangChain Agent  
→ OpenAI GPT model

Conversation Handling  
→ Stateful session memory  
→ Structured system prompt

---

# 🛠 Tech Stack

Python  
FastAPI  
Streamlit  
LangChain  
OpenAI API  
Pydantic  
Markdown  
Dotenv

---

# 📂 Project Structure

```
medconnect-ai
│
├── agent.py        # Streamlit conversational UI
├── app.py          # FastAPI backend API
├── demo_logic.py   # Fallback logic when API unavailable
├── .env            # Environment variables
├── requirements.txt
└── README.md
```

---

# ⚙️ Installation

Clone the repository:

```
git clone https://github.com/yourusername/medconnect-ai.git
cd medconnect-ai
```

Create a virtual environment:

```
python -m venv venv
```

Activate it:

Windows

```
venv\Scripts\activate
```

Install dependencies:

```
pip install -r requirements.txt
```

---

# 🔑 Environment Setup

Create a `.env` file and add:

```
OPENAI_API_KEY=your_openai_api_key
```

---

# ▶️ Running the Application

Start the FastAPI server:

```
uvicorn app:app --reload
```

Run the Streamlit interface:

```
streamlit run agent.py
```

---

# 💬 Example Interaction

User:
```
Hi, I have had a sore throat and fever for two days.
```

Assistant:
```
I'm sorry you're not feeling well. Could you please tell me your age and biological sex so I can guide you better?
```

After triage:

```
Based on your symptoms, our providers can assist you. 
Please book a telemedicine consultation using the link below.
```

---

# ⚠️ Medical Disclaimer

This project is a demonstration of conversational AI for healthcare triage.

It does not provide medical diagnosis and should not be used as a substitute for professional medical advice.

---

# 📈 Future Improvements

Doctor availability scheduling  
Electronic health record integration  
Voice-based interaction  
Medical knowledge base integration  
Multi-language support  
Advanced triage decision models

---

# 👩‍💻 Author

Developed as an AI healthcare assistant prototype demonstrating conversational triage systems and telemedicine integration.

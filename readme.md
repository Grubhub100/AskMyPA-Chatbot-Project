# AskMyPhysician Associate AI 🩺

Welcome to the **AskMyPhysician Associate AI**, a professional, empathetic, and intelligent medical symptom checker and triage assistant. This API is designed to guide patients through a structured triage process, identify potential emergencies, and seamlessly integrate with telemedicine booking platforms.

---

## 🚀 Features

- **Empathetic AI Persona**: Built with a kind and professional tone to build rapport with patients.
- **Smart Symptom Triage**: Guided interaction flow to collect essential clinical information:
  - Primary symptoms and duration.
  - Comprehensive review of associated symptoms.
  - **Mandatory** age and biological sex collection for accurate triage.
- **Emergency Detection**: Real-time identification of life-threatening symptoms (chest pain, difficulty breathing, etc.) with immediate 911/ER referral.
- **Service Scope Awareness**: Knowledgeable about specific treated conditions (Acute infections, Respiratory issues, Wellness, Lifestyle, etc.).
- **Nonsense/Gibberish Detection**: Politely handles typing mistakes or unclear input without losing context.
- **Telemedicine Integration**: Automatically provides booking links (Optimantra) only after full triage.
- **Multi-Format Support**: Handles both `JSON` and `Form-Data` requests for easy WordPress/Frontend integration.
- **Stateful Demo Mode**: Automatic fallback to a high-quality demo mode if the OpenAI API is unavailable or the quota is reached.

---

## 🛠️ Technology Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **AI Orchestration**: [LangChain](https://www.langchain.com/)
- **LLM**: OpenAI GPT-4o-mini
- **Environment Management**: `python-dotenv`
- **Frontend Compatibility**: CORS configured for WordPress and web integrations.

---

## 📋 Prerequisites

- Python 3.9+
- OpenAI API Key (Optional for Demo Mode)

---

## ⚙️ Setup & Installation

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd medical-chatbot
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   Create a `.env` file in the root directory (refer to `.env.example`):
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

---

## 🚀 Running the Application

Start the FastAPI server using Uvicorn:

```bash
uvicorn app:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

---

## 🔍 API Documentation

### POST `/chat`

Main endpoint for interacting with the AI Assistant.

**Request Body (JSON or Form Data):**

| Field | Type | Description |
| :--- | :--- | :--- |
| `message` | `string` | The user's input/symptom description. |
| `session_id` | `string` | (Optional) Unique ID to maintain conversation state. |
| `chat_history`| `list` | (Optional) List of previous messages for context. |

**Example Request:**
```json
{
  "message": "I've had a bad cough for 3 days",
  "session_id": "user_12345"
}
```

**Response:**
```json
{
  "status": "success",
  "response": "I'm sorry to hear about your cough. Have you also experienced any fever or body aches?",
  "session_id": "user_12345"
}
```

---

## 🌐 WordPress Integration

The API is specifically tuned to work with WordPress frontends.
- **CORS Support**: Pre-configured to accept requests from external domains.
- **Form Data Support**: Compatible with standard WordPress form submission methods.

---

## ⚠️ Medical Disclaimer

*This AI tool is for informational and triage purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of your physician or other qualified health provider with any questions you may have regarding a medical condition. If you are experiencing a medical emergency, call 911 immediately.*

---

Developed for **AskMyPhysician Associate**.

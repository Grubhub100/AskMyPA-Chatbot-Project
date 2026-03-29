import re
import config

BOOKING_LINK = config.LINKS["booking"]
TREATED_CONDITIONS = config.SERVICES["treated_conditions"]
ERROR_MESSAGE = config.MESSAGES["error"]

# Medical Safety Disclaimer
DISCLAIMER = f"\n\n***{config.MESSAGES['disclaimer']}***"

def get_demo_response(user_input: str, state: dict = None) -> (str, dict):
    """
    Hardened Triage Demo: Robust regex detection, emergency screening, and medical safety.
    """
    u_low = user_input.lower().strip()
    
    # --- 1. Emergency Screening (Critical Priority) ---
    emergency_keywords = [
        r"chest\s*(pain|hurt|pressure|tight)", 
        r"(difficulty|trouble|can'?t)\s*(breathing|breathe)", 
        r"shortness\s*of\s*breath",
        r"unconscious", r"passed\s*out", r"fainted",
        r"stroke", r"facial\s*droop", r"slurred\s*speech", r"arm\s*weakness",
        r"heavy\s*bleeding", r"bleeding\s*heavily",
        r"severe\s*allergic", r"throat\s*closing", r"anaphylaxis"
    ]
    if any(re.search(kw, u_low) for kw in emergency_keywords):
        return (
            "⚠️ **URGENT EMERGENCY**: Your symptoms indicate a high-risk medical condition. "
            "Please **immediately call 911** or go to the nearest Emergency Room. "
            "Do not wait for a consultation. Your safety is our priority.",
            state
        )

    # --- 2. Advanced Detection Helpers ---
    def detect_symptoms(text):
        symptom_patterns = [
            r"headach?e", r"pain", r"fever", r"cou?gh", r"sore", r"ache", r"stomach",
            r"hurt", r"burn", r"discomfort", r"sting", r"throb", r"itch", r"rash",
            r"swelling", r"nausea", r"vomit", r"dizz", r"tired", r"weak"
        ]
        return any(re.search(p, text) for p in symptom_patterns)

    def detect_duration(text):
        # Must have a number + digit or specific time keywords
        return bool(re.search(r"\b\d+\s*(day|hour|week|month)s?\b|\bsince\b|\byesterday\b", text))

    def detect_age(text):
        # Look for age patterns: "25 male", "32 years old", "age 40"
        # Match standalone 1-3 digit numbers BUT ensure it's not the duration number
        age_pattern = r"\b\d{1,3}\b"
        matches = re.findall(age_pattern, text)
        if not matches: return False
        
        # If there's a duration pattern, find the duration number and exclude it
        duration_match = re.search(r"(\b\d+)\s*(day|hour|week|month)s?\b", text)
        if duration_match:
            duration_num = duration_match.group(1)
            other_nums = [n for n in matches if n != duration_num]
            return len(other_nums) > 0
        return True

    def detect_sex(text):
        # Precise full words 'male' or 'female' only
        return bool(re.search(r"\b(male|female)\b", text)) and not re.search(r"male-ish|female-ish", text)

    # --- 3. Triage State/One-Shot Check ---
    s_found = detect_symptoms(u_low)
    d_found = detect_duration(u_low)
    a_found = detect_age(u_low)
    sex_found = detect_sex(u_low)

    if s_found and d_found and a_found and sex_found:
        return (
            f"Thank you for sharing those details. I'm sorry to hear you're feeling this way. 😔 "
            f"Based on your symptoms and the information provided, **a professional telemedicine consultation is recommended**.\n\n"
            f"👉 **[Book a Telemedicine Consultation]({BOOKING_LINK})**"
            f"{DISCLAIMER}",
            state
        )

    # --- 4. Keyword Triage Paths ---
    
    # Greetings
    if any(word == u_low or u_low.startswith(word + " ") for word in ["hi", "hello", "hey", "hii", "greetings"]):
        return "Hello! 👋 I'm your AI Symptom Checker. I'm here to help you understand your symptoms. How can I assist you today? Please describe what you're feeling.", state
    
    # Treated Conditions
    elif any(word in u_low for word in ["treat", "services", "provide", "offer", "help with", "can you do", "condition"]):
        return f"Our providers offer a wide range of services, including:\n{TREATED_CONDITIONS}\n\nHow can I help you feel better today?", state

    # Symptom Response
    elif s_found:
        return "I'm sorry you're feeling unwell. 😔 I want to help you get the right care. **How long have you been experiencing these symptoms?**", state
        
    # Duration Response
    elif d_found:
        return "Thank you for that information. It's helpful to know the timeline. Besides what you've mentioned, **are you experiencing any other discomfort or symptoms?**", state
        
    # No other symptoms
    elif u_low in ["no", "none", "no other symptoms", "nothing else"]:
        return "Understood. To complete my assessment, **could you please tell me your age and biological sex?** (e.g., '25, male')", state
        
    # Age & Sex Response (Stricter)
    elif a_found and sex_found:
        return (
            f"Thank you for providing those details. Based on our assessment, **a professional telemedicine consultation is recommended** to properly evaluate your condition.\n\n"
            f"👉 **[Book a Telemedicine Consultation]({BOOKING_LINK})**"
            f"{DISCLAIMER}",
            state
        )
    
    # Direct Booking
    elif any(word in u_low for word in ["book", "appointment", "doctor", "consultation"]):
        return f"Certainly! You can book your telemedicine consultation here: **[Book Now]({BOOKING_LINK})**{DISCLAIMER}", state

    # Fallback
    else:
        return ERROR_MESSAGE, state

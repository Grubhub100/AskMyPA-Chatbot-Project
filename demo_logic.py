import re
import config

BOOKING_LINK = config.BOOKING_LINK

def get_demo_response(user_input: str, state: dict = None) -> (str, dict):
    """
    Return a canned response and an updated state dictionary.
    Used when the OpenAI agent is unavailable.
    """
    u_low = user_input.lower().strip()
    
    # Initialize state if not provided
    if state is None:
        state = {
            "step": "idle",
            "user_symptoms": "",
            "duration_known": False
        }

    step = state.get("step", "idle")

    # --- Emergency check (always top priority) ---
    if any(s in u_low for s in config.SERIOUS_KEYWORDS):
        return "⚠️ **EMERGENCY**: Please call 911 or go to the ER immediately.", state

    # --- Pain Handling (User Request #6) ---
    if any(p in u_low for p in config.PAIN_KEYWORDS):
        return f"{config.PAIN_MESSAGE}\n\n{BOOKING_LINK}", state

    # --- Helper functions ---
    def has_symptoms(text):
        patterns = [
            r"\bfiv[eo]?r\b", r"\bfe?ve?r\b", r"\bcou?gh?\b", r"\bcold\b", r"\bflu\b",
            r"\bsick\b", r"\bill\b", r"\bunwell\b", r"\bpain\b", r"\bache\b",
            r"\bheadach?e?\b", r"\bnause?a?\b", r"\bvomit", r"\bdizz", r"\btired\b", r"\bweak\b",
            r"\bsore\b", r"\bthroat\b", r"\brash\b", r"\bitching\b", r"\bswelling\b",
            r"\bdischarg", r"\ballerg", r"\banxiet", r"\bdepress", r"\bsleep", r"\binfection\b",
            r"\bnot feeling", r"\bfeeling (bad|sick|unwell|awful|terrible)",
            r"\bsymptom", r"\bburning\b", r"\bchills?\b", r"\bshiver",
            r"\bstomach\b", r"\bblood\b", r"\bsweat",
            r"\bacne\b", r"\beczema\b", r"\basthma\b", r"\byeast\b", r"\bhormone\b", r"\bsexual\b",
            r"\bweight\b", r"\bglp-?1\b", r"\brefill\b", r"\burinary\b", r"\buti\b", r"\bsinus\b"
        ]
        return any(re.search(p, text) for p in patterns)

    def has_duration(text):
        patterns = [
            r"\d+\s*(day|hour|hr|week|wk|month|year)s?",
            r"\bsince\b", r"\byesterday\b",
            r"\blast (night|week|month)\b",
            r"\bfor (a|the|few)\b",
        ]
        return any(re.search(p, text) for p in patterns)

    def has_age(text):
        """Check for age patterns."""
        patterns = [
            r"\b\d{1,3}\s*(year|yr)s?\s*(old)?\b",
            r"\b\d{1,3}\b"
        ]
        return any(re.search(p, text) for p in patterns)

    def has_sex(text):
        """Check for biological sex patterns."""
        patterns = [
            r"\bmale\b", r"\bfemale\b",
            r"\bgirl\b", r"\bboy\b",
            r"\bwoman\b", r"\bman\b",
            r"\blady\b", r"\bgentleman\b",
            r"\b\d{1,3}\s*[mf]\b"
        ]
        return any(re.search(p, text) for p in patterns)

    def is_invalid_zero(text):
        """Reject zero/nonsensical values."""
        return (
            bool(re.fullmatch(r"0+\.?0*", text.strip())) or
            bool(re.search(r"\b0\s*(day|hour|hr|week|wk|month|yr|year)s?\b", text)) or
            bool(re.search(r"\b0+\s*(year|yr)s?\s*(old)?\b", text))
        )

    def is_gibberish(text):
        """Check for nonsensical characters or gibberish like '#@$@%' or 'dsg'."""
        # 1. Purely non-alphanumeric (e.g. #@$@%)
        if bool(re.fullmatch(r"[\W\d_]+", text)) and len(text) > 0:
            return True
        # 2. Very short and no vowels, but not 'no', 'none', 'na'
        if len(text.replace(" ", "")) < 3 and not any(v in text for v in "aeiouy") and text not in ["no", "na"]:
            return True
        # 3. No vowels in a longer string (e.g. 'dsg', 'qwrt')
        if not any(v in text for v in "aeiouy") and len(text) >= 3 and text not in ["none", "mhm", "brb"]:
            return True
        return False

    # --- Global Gibberish Check ---
    if is_gibberish(u_low):
        return "I'm sorry, I didn't quite understand that. It looks like there might be a typing mistake. Could you please describe your symptoms or how you're feeling so I can help? 🩺", state

    # --- Logic ---
    if step == "idle":
        # Check for ALL requirements at once (Symptoms + Duration + Age/Sex)
        s_found = has_symptoms(u_low)
        d_found = has_duration(u_low)
        a_found = has_age(u_low)
        sex_found = has_sex(u_low)

        if s_found:
            state["user_symptoms"] = u_low
            if d_found: state["duration_known"] = True

            if d_found and a_found and sex_found:
                state["step"] = "done"
                return (
                    f"Hello! 👋 Based on your symptoms and the details provided, **a professional telemedicine consultation is strongly recommended**.\n\n"
                    f"{BOOKING_LINK}",
                    state
                )
            
            # Start triage if not all info is present: Always check for more symptoms first
            state["step"] = "exploring_more"
            return (
                f"Hello! 👋 I'm sorry to hear you're not feeling well. 😔 "
                f"I see it's been going on for {u_low if d_found and not state['duration_known'] else 'a bit'}. "
                "I'd like to ask you a few questions to better understand your condition.\n\n"
                "Besides what you mentioned, **are you experiencing any other symptoms** "
                "such as body aches, chills, fatigue, or difficulty sleeping?",
                state
            )

        greetings = ["hi", "hello", "hey", "hii", "hi there", "hello there", "greetings"]
        if any(g == u_low or u_low.startswith(g + " ") for g in greetings):
            return "Hello! 👋 I'm your AI Symptom Checker by AskMyPA. How are you feeling today? Please describe your symptoms and I'll help guide you.", state

        provider_queries = ["treat", "services", "provide", "offer", "help with", "can you do"]
        if any(q in u_low for q in provider_queries):
            return (
                "Our providers offer a wide range of services, including:\n"
                "- **General health consultations**\n"
                "- **Acute symptoms**: Cold, flu, sore throat, sinus/ear infections, fever, pink eye, cough, allergies.\n"
                "- **Infections**: UTIs, yeast infections, minor skin issues (acne, eczema, rashes).\n"
                "- **Gastrointestinal**: Nausea, stomach pain, digestive issues.\n"
                "- **Mental health**: Support for stable minor depression/anxiety.\n"
                "- **Wellness**: Weight management (GLP-1), travel advice, vaccines, sexual health.\n"
                "- **Prescriptions**: Medication refills (unscheduled only).\n\n"
                "How can I assist you with your health today?",
                state
            )

        if any(b in u_low for b in config.BOOKING_INTENT_KEYWORDS):
            return f"I can certainly help you book an appointment. {BOOKING_LINK}", state

        return "I'm sorry, I didn't quite understand that. It looks like there might be a typing mistake. Could you please describe your symptoms or how you're feeling so I can help? 🩺", state

    if step == "exploring_more":
        state["user_symptoms"] += " | " + u_low
        state["step"] = "exploring_severity"
        return (
            "Thank you for sharing that. "
            "**On a scale of 1 to 10, how severe would you say your discomfort is?** "
            "And are these symptoms affecting your daily activities or sleep?",
            state
        )

    if step == "exploring_severity":
        if not re.search(r"\b([1-9]|10)\b", u_low):
            return "Please provide proper data including a severity rating on a scale of 1 to 10.", state

        if state["duration_known"]:
            state["step"] = "awaiting_age_sex"
            return "I see. To provide the most accurate guidance, **could you please tell me your age and biological sex?** (e.g. '32 years old, female')", state
        else:
            state["step"] = "awaiting_duration"
            return "I understand. **How long have you been experiencing these symptoms?** (e.g. '2 days', '1 week', 'since yesterday')", state

    if step == "awaiting_duration":
        if is_invalid_zero(u_low) or not has_duration(u_low):
            return (
                "That doesn't seem right. "
                "**Please provide proper data for your duration** — for example, '2 days', '1 week', or 'since yesterday'.",
                state
            )
        state["duration_known"] = True
        state["step"] = "awaiting_age_sex"
        return "Understood. To provide the most accurate guidance, **could you please tell me your age and biological sex?** (e.g. '32 years old, female')", state

    if step == "awaiting_age_sex":
        age_in = has_age(u_low)
        sex_in = has_sex(u_low)
        
        if is_invalid_zero(u_low) or not (age_in and sex_in):
            # Help the user by telling them what is missing
            missing = []
            if not age_in: missing.append("age")
            if not sex_in: missing.append("biological sex")
            
            missing_text = " and ".join(missing)
            
            return (
                f"I'm sorry, it looks like your **{missing_text}** is missing or was typed incorrectly. "
                "**Please provide both your age and biological sex** together so I can assist you properly "
                "(e.g., '32 years old, female').",
                state
            )
        state["step"] = "done"
        return (
            f"Thank you so much for sharing that information. 🙏 Based on your symptoms and everything "
            f"you've described, **a professional telemedicine consultation is strongly recommended**. "
            f"Our experienced medical team will properly evaluate your condition, provide a diagnosis, "
            f"and recommend the right treatment plan.\n\n"
            f"{BOOKING_LINK}\n\n"
            f"*Please don't delay — getting the right care early makes a big difference.*",
            state
        )

    if step == "done":
        if any(w in u_low for w in ["thank", "thanks", "ok", "okay", "great", "bye", "goodbye", "appreciate"]):
            return "You're welcome! 😊 Take care and feel better soon. Don't hesitate to reach out if you need anything else.", state
        return (
            f"I've already recommended a telemedicine consultation for your condition. "
            f"You can book your visit here: {BOOKING_LINK}\n\n"
            "Is there anything else I can help you with?",
            state
        )

    return "I'm here to help with your health concerns. Please describe your symptoms and I'll guide you. 🩺", state

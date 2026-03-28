# Global Configuration Settings

# --- Links ---
BOOKING_LINK = "https://www.optimantra.com/optimus/patient/patientaccess/servicesall?pid=U1o5cWpLTytaNDBMRU1DM1VRdE1ZZz09&lid=SWZ6WStZeWdvblZwMWJZQy96MUJkUT09"

# --- Messages ---
ERROR_MESSAGE = "We're having trouble processing your request. Please book a visit directly using the link below."

PAIN_MESSAGE = "We specialize in treating musculoskeletal pain and acute discomfort. Our providers can help evaluate your symptoms and provide a treatment plan. You can book a visit directly here: " + BOOKING_LINK

DEMO_RESPONSE_NOTE = "Note: Running in Demo Mode due to API issues."

# --- Treated Conditions ---
TREATED_CONDITIONS = """
Our providers offer a wide range of services, including:
- **General health consultations**
- **Management of acute symptoms**: Cold, flu-like symptoms, sore throat, sinus infection, ear infection, fever, pink eye, cough, allergies & hay fever.
- **Infections**: UTIs, vaginal discharge, yeast infections, minor skin issues (acne, eczema, rashes, minor cuts).
- **Gastrointestinal**: Nausea, vomiting, upset stomach, stomach pain, digestive issues.
- **Respiratory**: Asthma, allergies, or cough.
- **Pain Management**: painsEvaluation and treatment of various types of pain, including headaches,  musculoskeletalpain, muscle pain, joint pain, back pain, and other general or chronic pain conditions
- **Mental health support**: Stable conditions on medications (minor depression/anxiety).
- **Wellness & Lifestyle**: Weight management (GLP-1 prescription & lifestyle), coaching, international travel advice, vaccine recommendations, hormone imbalances, sexual health.
- **Medication refills**: Unscheduled prescriptions only.
- **Urgent Care**: If it's an urgent care complaint, our providers can help.
"""

# --- Keywords ---
PAIN_KEYWORDS = ["pain", "ache", "sore", "hurts", "throbbing", "stinging", "burning"]
SERIOUS_KEYWORDS = ["chest pain", "difficulty breathing", "stroke", "bleeding", "emergency"]
BOOKING_INTENT_KEYWORDS = ["book", "appointment", "see a doctor", "consultation", "visit"]

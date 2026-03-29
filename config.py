# config.py

LINKS = {
    "booking": "https://www.optimantra.com/optimus/patient/patientaccess/servicesall?pid=U1o5cWpLTytaNDBMRU1DM1VRdE1ZZz09&lid=SWZ6WStZeWdvblZwMWJZQy96MUJkUT09"
}

SERVICES = {
    "treated_conditions": """
Our providers offer a wide range of services, including:
- **General health consultations**
- **Management of acute symptoms**: Cold, flu-like symptoms, sore throat, sinus infection, ear infection, fever, pink eye, cough, allergies & hay fever.
- **Infections**: UTIs, vaginal discharge, yeast infections, minor skin infections (acne, eczema, rashes, minor cuts).
- **Gastrointestinal**: Nausea, vomiting, upset stomach, stomach pain, digestive issues.
- **Respiratory**: Asthma, allergies, or cough.
- **Mental health support**: Stable conditions on medications (minor depression/anxiety).
- **Wellness & Lifestyle**: Weight management (GLP-1 prescription & lifestyle), coaching, international travel advice, vaccine recommendations, hormone imbalances, sexual health.
- **Medication refills**: Unscheduled prescriptions only.
- **Urgent Care**: If it's an urgent care complaint, our providers can help.
- **Pain treatment or management**: We specialize in musculoskeletal pain and chronic pain management.
"""
}

MESSAGES = {
    "pain": "I understand you're experiencing pain. For musculoskeletal concerns or acute pain management, our providers can help you directly.",
    "error": f"We're having trouble processing your request. Please book a visit directly here: [Book a Telemedicine Consultation]({LINKS['booking']})",
    "demo_note": "Running in Demo Mode due to API issues",
    "disclaimer": "Note: This system provides guidance based on symptoms and is NOT a medical diagnosis. A professional consultation is highly recommended."
}

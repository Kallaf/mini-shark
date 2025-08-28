import streamlit as st
import google.generativeai as genai
import os

# --- Configuration ---
# Make sure to set your GOOGLE_API_KEY as an environment variable
# For Streamlit Cloud, set it in the secrets management.
# For local development, you can use a .env file and python-dotenv
try:
    # Attempt to get the API key from Streamlit secrets
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    # If not found, try getting it from environment variables
    # This is useful for local development.
    from dotenv import load_dotenv
    load_dotenv()
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error("Google API Key not found. Please set the GOOGLE_API_KEY environment variable or add it to your Streamlit secrets.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# --- Shark Persona and Portfolio ---
SHARK_PERSONA = {
    "name": "Mr. Wonderful (Kevin O'Leary)",
    "bio": "I'm not here to make friends; I'm here to make money. I'm a no-nonsense investor with a keen eye for businesses that have a clear path to profitability. I'm known for my love of royalty deals and my brutal honesty. Don't waste my time with fluff.",
    "investment_philosophy": "I look for businesses with strong fundamentals, a clear value proposition, and a scalable model. I'm particularly interested in recurring revenue streams and licensing opportunities. I'm not afraid to be tough, but I'm fair.",
    "current_portfolio": ["Blueland", "Lovepop", "Snarky Tea", "Pulp Pantry"],
    "cash_on_hand": "$100,000,000",
    "areas_of_expertise": ["Software", "Consumer Goods", "Financial Services", "Licensing"],
}

# --- Conversation Stages ---
STAGES = {
    1: "hearing_pitch",
    2: "asking_questions",
    3: "making_decision",
    4: "negotiating",
}

# --- Gemini Model ---
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Streamlit App ---
st.set_page_config(page_title="Shark Tank AI", page_icon="🦈")

st.title("🦈 Shark Tank AI")
st.write(f"You are pitching to **{SHARK_PERSONA['name']}**.")
st.write(SHARK_PERSONA['bio'])

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "stage" not in st.session_state:
    st.session_state.stage = 1

# --- Display Chat History ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Main Chat Logic ---
if prompt := st.chat_input("What is your pitch?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # Construct the context for the Gemini model
        context = f"You are {SHARK_PERSONA['name']}. Your persona is: {SHARK_PERSONA['bio']}. Your investment philosophy is: {SHARK_PERSONA['investment_philosophy']}. Your areas of expertise are: {', '.join(SHARK_PERSONA['areas_of_expertise'])}. You are currently in stage {st.session_state.stage} of the conversation: {STAGES[st.session_state.stage]}."

        # Add conversation history to the context
        for message in st.session_state.messages:
            context += f"\n{message['role']}: {message['content']}"

        # Add the current prompt to the context
        context += f"\nuser: {prompt}"

        # Generate the response from the Gemini model
        try:
            response = model.generate_content(context)
            full_response = response.text
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.stop()


        message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # --- Stage Progression Logic ---
    if st.session_state.stage == 1 and len(st.session_state.messages) > 2:
        st.session_state.stage = 2
    elif st.session_state.stage == 2 and "offer" in full_response.lower():
        st.session_state.stage = 3
    elif st.session_state.stage == 3 and ("accept" in prompt.lower() or "deal" in prompt.lower()):
        st.session_state.stage = 4
    elif "out" in full_response.lower():
        st.warning("Mr. Wonderful is out. The conversation has ended.")

# --- Sidebar with Shark Info ---
with st.sidebar:
    st.header("Shark Profile")
    st.subheader(SHARK_PERSONA["name"])
    st.write(f"**Cash on Hand:** {SHARK_PERSONA['cash_on_hand']}")
    st.write("**Areas of Expertise:**")
    for area in SHARK_PERSONA["areas_of_expertise"]:
        st.write(f"- {area}")
    st.write("**Current Portfolio:**")
    for investment in SHARK_PERSONA["current_portfolio"]:
        st.write(f"- {investment}")

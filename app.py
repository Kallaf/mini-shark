import streamlit as st
import google.generativeai as genai
import os
import re
import json

# --- Configuration ---
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except (FileNotFoundError, KeyError):
    from dotenv import load_dotenv
    load_dotenv()
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    st.error("Google API Key not found.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# --- Shark Persona ---
SHARK_PERSONA = {
    "name": "Mr. Wonderful (Kevin O'Leary)",
    "bio": "I'm not here to make friends; I'm here to make money...",
    "investment_philosophy": "I look for businesses with strong fundamentals...",
    "current_portfolio": ["Blueland", "Lovepop", "Snarky Tea", "Pulp Pantry"],
    "cash_on_hand": "$100,000,000",
    "areas_of_expertise": ["Software", "Consumer Goods", "Financial Services", "Licensing"],
}

# --- Checklist ---
REQUIRED_INFO = {
    "valuation": False,
    "equity": False,
    "revenue": False,
    "grossMargin": False,
    "customerAcquisitionCost": False,
    "netProfit": False,
    "scalability": False,
    "licensing": False,
}

# --- Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "stage" not in st.session_state:
    st.session_state.stage = 1
if "shark_typing" not in st.session_state:
    st.session_state.shark_typing = False
if "final_report" not in st.session_state:
    st.session_state.final_report = None

# --- Gemini Model ---
model = genai.GenerativeModel('gemini-1.5-flash')

# --- Utility: Extract JSON ---
def extract_json(text):
    try:
        json_start = text.find('{')
        json_end = text.rfind('}')
        if json_start == -1 or json_end == -1:
            raise ValueError("No JSON object found.")
        json_str = text[json_start:json_end+1]
        return json.loads(json_str)
    except Exception as e:
        st.error(f"⚠️ Failed to parse JSON: {e}")
        return None

# --- Format Final Report ---
def format_final_report(raw_text):
    lines = raw_text.strip().split("\n")
    html = ""
    for line in lines:
        if line.startswith("- "):
            html += f"<li>{line[2:].strip()}</li>"
        elif line.strip() == "":
            html += "<br>"
        else:
            html += f"<h4>{line.strip()}</h4>"
    return f"<div style='padding:1rem;background:#f9f9f9;border-radius:8px;'>{html}</div>"

# --- Final Report Generator ---
def generate_final_report():
    history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
    report_prompt = f"""
Summarize the Shark Tank pitch session in a structured report. Include:

- Entrepreneur name (if mentioned)
- Business idea and value proposition
- Key metrics discussed (valuation, revenue, margins, etc.)
- Shark's reactions and questions
- Final decision and terms (if any)
- Investor advice or closing remarks

Conversation history:
{history}
"""
    try:
        report_response = model.generate_content(report_prompt)
        st.session_state.final_report = report_response.text
    except Exception as e:
        st.error("Failed to generate final report.")

# --- Streamlit Setup ---
st.set_page_config(page_title="Shark Tank AI", page_icon="🦈", layout="wide")
st.title("🦈 Shark Tank AI")

# --- Shark Intro ---
st.write(f"You are pitching to **{SHARK_PERSONA['name']}**.")
st.write(SHARK_PERSONA['bio'])

# --- Display Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Final Report View ---
prompt = None
if st.session_state.final_report:
    st.divider()
    st.subheader("📊 Final Pitch Report")
    st.markdown(format_final_report(st.session_state.final_report), unsafe_allow_html=True)
else:
    if not st.session_state.shark_typing:
        prompt = st.chat_input("What is your pitch?")
    else:
        st.chat_input("Shark is thinking...", disabled=True)

# --- Main Logic ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.shark_typing = True
    st.rerun()

if st.session_state.shark_typing:
    with st.chat_message("assistant"):
        with st.spinner("Mr. Wonderful is thinking..."):
            history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
            checklist_json = json.dumps(REQUIRED_INFO)

            full_prompt = f"""
You are {SHARK_PERSONA['name']}, a tough investor on Shark Tank. Respond in the following JSON format only:

{{
  "currentState": <int>,  // 1 = hearing_pitch, 2 = asking_questions, 3 = making_decision, 4 = negotiating
  "message": "<Your response to the user>",
  "sharkReaction": "<Enum: impressed | skeptical | annoyed | intrigued | neutral>",
  "checklistUpdate": {{
    "valuation": <true|false>,
    "equity": <true|false>,
    "revenue": <true|false>,
    "grossMargin": <true|false>,
    "customerAcquisitionCost": <true|false>,
    "netProfit": <true|false>,
    "scalability": <true|false>,
    "licensing": <true|false>
  }},
  "decision": "<offer|pass|null>"
}}

Do not include any explanation outside the JSON. Use checklistUpdate to mark which items were covered in this turn.

Conversation history:
{history}

Current checklist status:
{checklist_json}

User: {st.session_state.messages[-1]['content']}
"""

            try:
                response = model.generate_content(full_prompt)
                raw_text = response.text
                shark_data = extract_json(raw_text)
                if not shark_data:
                    st.session_state.shark_typing = False
                    st.stop()
            except Exception as e:
                st.error(f"Unexpected error: {e}")
                st.session_state.shark_typing = False
                st.stop()

            # Display shark message
            st.markdown(shark_data["message"])
            st.session_state.messages.append({"role": "assistant", "content": shark_data["message"]})

            # Update checklist
            for key, value in shark_data["checklistUpdate"].items():
                REQUIRED_INFO[key] = value

            # Update stage
            st.session_state.stage = shark_data["currentState"]

            # Handle decision
            decision = shark_data["decision"]
            user_response = st.session_state.messages[-2]["content"].lower()

            if decision == "pass":
                st.warning("Mr. Wonderful is out. The conversation has ended.")
                generate_final_report()
            elif decision == "offer" and ("accept" in user_response or "deal" in user_response):
                st.success("💰 Deal accepted!")
                generate_final_report()

            # Optional UI reaction
            reaction = shark_data["sharkReaction"]
            if reaction == "skeptical":
                st.info("Mr. Wonderful looks unconvinced 😒")
            elif reaction == "impressed":
                st.balloons()
            elif reaction == "annoyed":
                st.error("He's losing patience 😤")
            elif reaction == "intrigued":
                st.success("You've piqued his interest 👀")

            st.session_state.shark_typing = False
            st.rerun()

# --- Sidebar ---
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

    st.divider()
    st.header("Pitch Checklist")
    for term, covered in REQUIRED_INFO.items():
        status = "✅" if covered else "❌"
        st.write(f"{status} {term}")

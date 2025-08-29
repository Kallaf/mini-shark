import streamlit as st
from config import SHARK_PERSONA
from state import init_session
from prompts import build_prompt
from llm import setup_llm, get_shark_response
from report import generate_report, format_report
from ui import render_sidebar
from utils import extract_json

# --- Initialize ---
init_session()
model = setup_llm()
render_sidebar(st.session_state.checklist)

# --- Display Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Final Report View ---
if st.session_state.final_report:
    st.divider()
    st.subheader("📊 Final Pitch Report")
    st.markdown(format_report(st.session_state.final_report), unsafe_allow_html=True)
    st.stop()

# --- Chat Input ---
prompt = None
if not st.session_state.shark_typing:
    prompt = st.chat_input("What is your pitch?")
else:
    st.chat_input("Shark is thinking...", disabled=True)

# --- Handle New Prompt ---
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.shark_typing = True
    st.session_state.latest_prompt = prompt  # Store for later use
    st.rerun()

# --- Generate Shark Response ---
if st.session_state.shark_typing:
    with st.chat_message("assistant"):
        with st.spinner("Mr. Wonderful is thinking..."):
            history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
            full_prompt = build_prompt(
                history,
                st.session_state.checklist,
                st.session_state.latest_prompt,
                SHARK_PERSONA
            )

            shark_data = get_shark_response(model, full_prompt)
            if not shark_data:
                st.session_state.shark_typing = False
                st.stop()

            # Display shark message
            st.markdown(shark_data["message"])
            st.session_state.messages.append({"role": "assistant", "content": shark_data["message"]})

            # Update checklist
            for key, value in shark_data["checklistUpdate"].items():
                if value:
                    st.session_state.checklist[key] = value

            # Update stage
            st.session_state.stage = shark_data["currentState"]

            # Handle decision
            state = shark_data["currentState"]

            if state == "end":
                decision = shark_data["decision"]
                if decision == "pass":
                    st.warning("Mr. Wonderful is out. The conversation has ended.")
                    st.session_state.final_report = generate_report(model, history)

                elif decision == "offer":
                    st.success("💰 Deal accepted!")
                    st.session_state.final_report = generate_report(model, history)


            st.session_state.shark_typing = False
            st.rerun()

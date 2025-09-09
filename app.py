import streamlit as st
from config import SHARK_PERSONA
from state import init_session
from prompts import build_conversation_prompt, build_negotiation_prompt
from llm import setup_llm, get_shark_response
from report import generate_report, format_report
from ui import render_sidebar
from scoring_engine import ScoringEngine, shark1_decision
from negotiation_engine import NegotiationEngine

# --- Initialize ---
init_session()
model = setup_llm()
render_sidebar()

# Set initial stage to "q&a" if not set
if "stage" not in st.session_state or st.session_state.stage not in ["q&a", "negotiation", "end"]:
    st.session_state.stage = "q&a"


# Initialize scoring engine in session state
if "scoring_engine" not in st.session_state:
    st.session_state.scoring_engine = ScoringEngine()

# Initialize negotiation engine in session state
if "negotiation_engine" not in st.session_state:
    st.session_state.negotiation_engine = NegotiationEngine({
        "Out": 1,
        "Bad offer (don't negotiate much)": 3,
        "Fair but slightly low offer (light negotiation)": 5,
        "Good offer + upsell yourself": 7
    })

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
            print("Stage:", st.session_state.stage)  # Debugging line
            if "summary" not in st.session_state:
                st.session_state.summary = None
            history = st.session_state.summary if st.session_state.summary else "No prior conversation."

            # Q&A (conversation) phase
            if st.session_state.stage == "q&a":
                full_prompt = build_conversation_prompt(
                    history,
                    st.session_state.latest_prompt,
                    SHARK_PERSONA
                )
                shark_data = get_shark_response(model, full_prompt)
                
                print("Shark data:", shark_data)  # Debugging line
                print("---------------------------------------" * 3)  # Separator for clarity
                if not shark_data:
                    st.session_state.shark_typing = False
                    st.stop()

                # Scoring system logic
                scoring = shark_data["scoring_params"]
                st.session_state.scoring_engine.update(scoring)
                grade = st.session_state.scoring_engine.final_grade()
                decision = shark1_decision(grade)

                st.session_state.summary = shark_data.get("summary", st.session_state.summary)
                st.markdown(shark_data["message"])
                st.session_state.messages.append({"role": "assistant", "content": shark_data["message"]})

                # If end_negotiation is True, end the conversation and show report
                if shark_data.get("end_negotiation") is True:
                    st.warning("Negotiation ended by Shark. The conversation has ended.")
                    st.session_state.final_report = generate_report(model, st.session_state.summary)
                    st.session_state.shark_typing = False
                    st.rerun()

                # If scoring engine made a decision, move to negotiation
                elif st.session_state.scoring_engine.is_done():
                    st.session_state.stage = "negotiation"
                    st.session_state.decision = decision
                    st.session_state.negotiation_count = 0
                    # Optionally, set invest/not_invest reasons here
                    st.session_state.invest_reasons = scoring.get("pros", [])
                    st.session_state.not_invest_reasons = scoring.get("cons", [])
                    st.rerun()
                else:
                    st.session_state.shark_typing = False
                    st.rerun()

            # Negotiation phase
            elif st.session_state.stage == "negotiation":
                summary = st.session_state.summary if st.session_state.summary else "No prior conversation."
                negotiation_count = st.session_state.get("negotiation_count", 0)
                invest_reasons = st.session_state.get("invest_reasons", [])
                not_invest_reasons = st.session_state.get("not_invest_reasons", [])
                decision = st.session_state.get("decision", "Bad offer (don't negotiate much)")
                print(f"Negotiation count: {negotiation_count}, Current decision: {decision}, Invest reasons: {invest_reasons}, Not invest reasons: {not_invest_reasons}")  # Debugging line

                # Use negotiation engine to determine warning or out state
                negotiation_state = st.session_state.negotiation_engine.negotiate(decision)
                print(f"Negotiation state: {negotiation_state}")  # Debugging line
                show_last_warning = negotiation_state == 'warning'
                if negotiation_state == 'out':
                    decision = "out"

                full_prompt = build_negotiation_prompt(
                    decision, invest_reasons, not_invest_reasons, SHARK_PERSONA, show_last_warning, summary
                )
                st.session_state.negotiation_count = negotiation_count + 1

                shark_data = get_shark_response(model, full_prompt)
                print("Shark data:", shark_data)  # Debugging line
                print("---------------------------------------" * 3)  # Separator for clarity
                if not shark_data:
                    st.session_state.shark_typing = False
                    st.stop()

                st.session_state.summary = shark_data.get("summary", st.session_state.summary)
                st.markdown(shark_data["message"])
                st.session_state.messages.append({"role": "assistant", "content": shark_data["message"]})

                # Handle offer accepted
                if shark_data.get("offer_accepted") is True:
                    st.success("💰 Offer accepted! The negotiation has ended.")
                    st.session_state.final_report = generate_report(model, summary)
                    st.session_state.shark_typing = False
                    st.rerun()

                print("Decision after negotiation:", decision)
                # End negotiation if decision is out or negotiation limit reached
                if decision == "out":
                    st.warning("Mr. Wonderful is out. The conversation has ended.")
                    st.session_state.final_report = generate_report(model, summary)
                    st.session_state.shark_typing = False
                    st.rerun()

                st.session_state.shark_typing = False
                st.rerun()
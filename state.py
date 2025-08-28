import streamlit as st
from config import REQUIRED_INFO

def init_session():
    defaults = {
        "messages": [],
        "stage": 1,
        "shark_typing": False,
        "final_report": None,
        "checklist": REQUIRED_INFO.copy()
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

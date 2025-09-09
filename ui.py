import streamlit as st
from config import SHARK_PERSONA

def render_sidebar():
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

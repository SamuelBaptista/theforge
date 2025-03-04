import os
import streamlit as st

from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="Login",
    page_icon="🔑",
    layout="centered",
)

st.image("server/assets/images/arion_logo.png", use_container_width=True)
st.divider()

# Initialize authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

PASSWORD = os.getenv("STREAMLIT_PASSWORD")

def check_authentication():

    if not st.session_state.authenticated:

        token = st.text_input("Enter access password", type="password")

        if st.button("Login"):
            if token == PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid token")

        st.stop()

# Main app
st.title("Login")
check_authentication()

# Main page content
st.write("Welcome to arionkoder communication agent experiment!")

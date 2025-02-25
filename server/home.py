import streamlit as st
import requests

def homepage():
    st.set_page_config(
        page_title="Voice Precision Demo",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # --- Header Section ---
    st.markdown("# 🚑 Precision Voice Systems for Healthcare")
    st.markdown("---")

    # --- Introduction ---
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### Transcription-Based System (Text-Centric Pipeline)
        - **Multi-Step Process**    
        - **Limited Audio Control**  
        - **Intermediate Reasoning Flexibility** 
        - **Higher Latency**
        """)

    with col2:
        st.markdown("""
        ### Audio-Native Model (End-to-End Audio Processing)
        - **Direct Audio Handling**
        - **Real-Time Audio Control** 
        - **Seamless Output**  
        - **Minimal Reasoning Intermediacy**  
        - **Lower Latency**
        """)

    # --- Solution Showcase ---

    st.divider()
    
    with st.container():
        sol1, sol2, sol3 = st.columns(3)
        with sol1:
            st.markdown("### 🛠️ Function Calling Solution")
            st.markdown("""
            - Transcription-based system
            - Fast-path for common names  
            - SMS confirmation fallback
            """)

            st.markdown("### Basic Implementation")
            if st.button("View Function Calling Demo", key="tools"):
                st.switch_page("pages/tools.py")            
            
        with sol2:
            st.markdown("### 🔊 Real-Time Conversation")

            st.markdown("""
            - Audio-native model
            - Accent adaptation engine  
            - Dynamic speed detection  
            - Instant spelling mode  
            """)

            st.markdown("### Enhanced Audio AI")
            if st.button("Try Real-Time Model", key="realtime"):
                st.switch_page("pages/realtime.py")
        with sol3:

            st.markdown("### 📞 Phone call")

            st.markdown("""
            - Real phone call to test the system
            """)

            phone = st.text_input("Phone", value="+5519999872145")

            if st.button("Make call"):

                payload = {
                    "phone_number_to_call": phone,
                }

                requests.post("http://localhost:8000/make-call", json=payload)                                           

    # --- Footer ---
    st.markdown("---")
    st.caption("Developed for The Forge 25.1 | Spike | Voice Recognition & Generation")

if __name__ == "__main__":
    homepage()
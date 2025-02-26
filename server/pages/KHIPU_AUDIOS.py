import os
import io
import zipfile
import streamlit as st

st.set_page_config(
    page_title="KIPUH - Saved Audios",
    layout="centered",
    initial_sidebar_state="auto"
)

st.title("Saved Conversations")
st.divider()

# Path to audios directory
audio_dir = "server/assets/audios"

# Get all .wav files from the directory
audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]

if not audio_files:
    st.info("No audio files found in the directory.")
else:
    # Create a dictionary mapping display names to filenames
    audio_options = {}
    for audio_file in audio_files:
        name, country, _ = audio_file.rsplit('_', 2)
        display_name = f"{name} from {country}"
        audio_options[display_name] = audio_file
    
    # Create select box
    selected_audio = st.selectbox(
        "Select a conversation to play",
        options=list(audio_options.keys())
    )
    
    # Display selected audio
    if selected_audio:
        audio_file = audio_options[selected_audio]
        name, country, _ = audio_file.rsplit('_', 2)
        
        with st.container():
            
            audio_path = os.path.join(audio_dir, audio_file)
            with open(audio_path, 'rb') as audio_file:
                audio_bytes = audio_file.read()
                st.audio(audio_bytes)
            
            st.divider()


    # Create a ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for audio_file in os.listdir(audio_dir):
            if audio_file.endswith('.wav'):
                file_path = os.path.join(audio_dir, audio_file)
                zip_file.write(file_path, audio_file)
    
    # Create the download button
    st.download_button(
        label="Click to Download All Audio Files", 
        data=zip_buffer.getvalue(),
        file_name="all_audio_files.zip",
        mime="application/zip"
    )

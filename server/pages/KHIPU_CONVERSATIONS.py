import os
import io
import zipfile
import json

import streamlit as st


if not st.session_state.get('authenticated', False):
    st.warning("Please login at the login page")
    st.stop()

st.set_page_config(
    page_title="KIPUH - Saved Audios",
    layout="centered",
    initial_sidebar_state="auto"
)

st.title("Saved Conversations")
st.divider()

# Add download button for all files
def create_zip_of_all_files():
    audio_dir = "server/assets/audios"
    transcription_dir = "server/assets/transcriptions"
    evaluation_dir = "server/assets/evaluations"
    
    # Create a BytesIO object to store the zip file
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add audio files
        if os.path.exists(audio_dir):
            for file in os.listdir(audio_dir):
                if file.endswith('.wav'):
                    file_path = os.path.join(audio_dir, file)
                    zip_file.write(file_path, os.path.join("audios", file))
        
        # Add transcription files
        if os.path.exists(transcription_dir):
            for file in os.listdir(transcription_dir):
                if file.endswith('.json'):
                    file_path = os.path.join(transcription_dir, file)
                    zip_file.write(file_path, os.path.join("transcriptions", file))

        # Add evaluation files
        if os.path.exists(evaluation_dir):
            for file in os.listdir(evaluation_dir):
                if file.endswith('.json'):
                    file_path = os.path.join(evaluation_dir, file)
                    zip_file.write(file_path, os.path.join("evaluation", file))
    
    return zip_buffer.getvalue()

st.header("Audios")
audio_dir = "server/assets/audios"
transcription_dir = "server/assets/transcriptions"

if not os.path.exists(audio_dir):
    os.makedirs(audio_dir)
if not os.path.exists(transcription_dir):
    os.makedirs(transcription_dir)

# Get all .wav files from the directory
audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]

if not audio_files:
    st.info("No audio files found in the directory.")
else:
    # Create a dictionary mapping display names to filenames
    audio_options = {}
    for i, audio_file in enumerate(audio_files):
        name, accent, _ = audio_file.rsplit('_', 2)
        display_name = f"{i} - Name: {name} | Accent: {accent}"
        audio_options[display_name] = audio_file
    
    # Create a selectbox for the user to choose an audio file
    selected_display_name = st.selectbox("Select an audio file:", list(audio_options.keys()))
    selected_audio_file = audio_options[selected_display_name]
    
    # Display the audio file
    audio_path = os.path.join(audio_dir, selected_audio_file)
    st.audio(audio_path)
    
    # Get corresponding transcription file
    transcription_file = selected_audio_file.replace('.wav', '.json')
    transcription_path = os.path.join(transcription_dir, transcription_file)
    
    # Check if transcription exists and display it in an expander
    if os.path.exists(transcription_path):
        with open(transcription_path, 'r') as f:
            transcription_text = json.loads(f.read())
        
        with st.popover("Show Transcription"):
            for message in transcription_text:
                with st.chat_message(message['role']):
                    if message['role'] == "assistant":
                        content = json.loads(message['content'])
                        st.write(content['message'])
                    else:
                        st.write(message['content'])
    else:
        st.warning(f"No transcription found for {selected_audio_file}")

st.divider()

# Add download button at the top
zip_data = create_zip_of_all_files()
st.download_button(
    label="Download Files",
    data=zip_data,
    file_name="khipu_conversations.zip",
    mime="application/zip"
)
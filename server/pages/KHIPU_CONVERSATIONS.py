import os
import io
import zipfile
import json
import streamlit as st

st.set_page_config(
    page_title="KIPUH - Saved Audios",
    layout="centered",
    initial_sidebar_state="auto"
)

st.title("Saved Conversations")
st.divider()

st.header("Audios")
audio_dir = "server/assets/audios"

if not os.path.exists(audio_dir):
    os.makedirs(audio_dir)

# Get all .wav files from the directory
audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]

if not audio_files:
    st.info("No audio files found in the directory.")
else:
    # Create a dictionary mapping display names to filenames
    audio_options = {}
    for i, audio_file in enumerate(audio_files):
        first_name, last_name, accent, _ = audio_file.rsplit('_', 3)
        display_name = f"{i} - Name: {first_name} {last_name} - Accent: {accent}"
        audio_options[display_name] = audio_file
    
    # Create select box
    selected_audio = st.selectbox(
        "Select a conversation to play",
        options=list(audio_options.keys())
    )
    
    # Display selected audio
    if selected_audio:
        audio_file = audio_options[selected_audio]
        
        with st.container():
            
            audio_path = os.path.join(audio_dir, audio_file)
            
            with open(audio_path, 'rb') as audio_file:
                audio_bytes = audio_file.read()
                st.audio(audio_bytes)

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

st.divider()

st.header("Transcriptions")
transcription_dir = "server/assets/transcriptions"

if not os.path.exists(transcription_dir):
    os.makedirs(transcription_dir)

# Get all .txt files from the directory
transcription_files = [f for f in os.listdir(transcription_dir) if f.endswith('.json')]

if not transcription_files:
    st.info("No transcription files found in the directory.")
else:
    # Create a dictionary mapping display names to filenames
    transcription_options = {}
    for i, transcription_file in enumerate(transcription_files):
        first_name, last_name, accent, _ = transcription_file.rsplit('_', 3)
        display_name = f"{i} - Name: {first_name} {last_name} - Accent: {accent}"
        transcription_options[display_name] = transcription_file
    
    # Create select box
    selected_transcription = st.selectbox(
        "Select a conversation to view",
        options=list(transcription_options.keys())
    )
    
    # Display selected transcription
    if selected_transcription:
        transcription_file = transcription_options[selected_transcription]
        transcription_path = os.path.join(transcription_dir, transcription_file)
            
        with open(transcription_path, 'rb') as file:
            transcription_json = json.loads(file.read())
        
        if transcription_json:
            for i, message in enumerate(transcription_json):
                with st.chat_message(message['role']):
                    if message['role'] == "assistant":
                        content = json.loads(message['content'])
                        st.write(content['message'])
                    else:
                        st.write(message['content'])

    # Create a ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for transcription_file in os.listdir(transcription_dir):
            if transcription_file.endswith('.json'):
                file_path = os.path.join(transcription_dir, transcription_file)
                zip_file.write(file_path, transcription_file)
    
    # Create the download button
    st.download_button(
        label="Click to Download All Transcription Files", 
        data=zip_buffer.getvalue(),
        file_name="all_transcription_files.zip",
        mime="application/zip"
    )


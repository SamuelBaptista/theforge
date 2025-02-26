import time
import json
import uuid
import os
import io

import streamlit as st

from pydantic import BaseModel
from pydub import AudioSegment

from repenseai.genai.agent import Agent
from repenseai.genai.tasks.api import Task

from server.prompts.user_call_no_tools import instruction


st.set_page_config(
    page_title="KIPUH - STT, Reasoning, TTS",
    layout="centered",
    initial_sidebar_state="auto"
)


# FUNCTIONS

def combine_audio_segments(audio_segments: list):
    combined_audio = AudioSegment.empty()
    
    for segment in audio_segments:
        if isinstance(segment, bytes):
            audio_file = io.BytesIO(segment)
            audio = AudioSegment.from_file(audio_file)
        else:
            audio = AudioSegment(data=segment, sample_width=2, frame_rate=44100, channels=2)
        
        combined_audio += audio

    return combined_audio

def save_audio_to_disk(audio: AudioSegment, file_path: str):
    # Ensure the directory exists
    directory = os.path.dirname(file_path)
    os.makedirs(directory, exist_ok=True)
    
    # Save the audio file
    audio.export(file_path, format="wav")

def generate_voice(text: str):
    agent = Agent(
        model="tts-1-hd", 
        model_type="speech",
        voice="shimmer",
    )

    task = Task(
        agent=agent,
        speech_key="speech",
        simple_response=True
    )

    response = task.run({"speech": text})
    return response

def get_trascription(audio: bytes):
    t_agent = Agent(model="whisper-1", model_type="audio")
    t_task = Task(agent=t_agent, simple_response=True)

    t_response = t_task.run({"audio": audio})
    return t_response


# INTRO

st.title("Tool Usage Demo")
st.divider()

cols = st.columns(2)

with cols[0]:
    st.markdown("Let's test if our model can get your last name!")

    name = st.text_input("Enter your name")
    country = st.text_input("Enter your country")

with cols[1]:
    st.image("server/assets/STT-Reasoning-TTS.png", width=300)

# PAGE

if "task" not in st.session_state:

    class LLMResponse(BaseModel):
        message: str
        continue_chat: bool  

    agent = Agent(
        model="gpt-4o", 
        model_type="chat",
    )

    task = Task(
        user=instruction,
        agent=agent, 
        simple_response=True,
    )

    st.session_state.task = task

if "run" not in st.session_state:
    st.session_state.run = False

if "assistant" not in st.session_state:
    st.session_state.assistant = []

if "response" not in st.session_state:
    st.session_state.response = None

if "user" not in st.session_state:
    st.session_state.user = []

if "turn" not in st.session_state:
    st.session_state.turn = True

if "audio" not in st.session_state:
    st.session_state.audio = None

if "end" not in st.session_state:
    st.session_state.end = False

if 'name' not in st.session_state:
    st.session_state.name = None

if 'country' not in st.session_state:
    st.session_state.country = None

cols = st.columns(2)

st.divider()
st.write("### Task - Debuguer")
st.write(st.session_state.task.prompt)
st.write(st.session_state.response)

if cols[1].button("Reset", use_container_width=True, type='primary'):
    st.session_state.run = False

    for key in st.session_state:
        if key not in ["task", "run"]:
            del st.session_state[key]

    st.rerun()

if cols[0].button("Run", use_container_width=True) or st.session_state.run:
    st.session_state.run = True

    st.session_state.name = name
    st.session_state.country = country

    st.divider()

    if st.session_state.assistant and not st.session_state.turn:
        with st.chat_message("assistant"):
            st.audio(st.session_state.assistant[-1], autoplay=True)    

    if st.session_state.end:
        with st.chat_message("assistant"):
            st.audio(st.session_state.assistant[-1], autoplay=True)
            
        time.sleep(12)

        final_chat = []

        for u, a in zip(st.session_state.user, st.session_state.assistant):
            final_chat.append(a)
            final_chat.append(u)
            
        final_chat.append(st.session_state.assistant[-1])
        full_audio = combine_audio_segments(final_chat)

        save_audio_to_disk(
            full_audio, 
            f"assets/audios/{st.session_state.name}_{st.session_state.country}_{str(uuid.uuid4())}.wav"
        )

        st.write("### End of the conversation")
        st.write("Thank you for participating in this demo.")
        
        st.stop()

    st.divider()

    if st.session_state.turn:

        context = {
            "user_data": {
                "name": st.session_state.name,
                "country": st.session_state.country
            },
            "missing_data": "last name"
        }

        response = st.session_state.task.run(context)
        try:
            st.session_state.response = json.loads(response)
        except TypeError:
            print(response)
            st.session_state.response = response
        except json.JSONDecodeError:

            st.session_state.response = {}

            st.session_state.response['continue_chat'] = True
            st.session_state.response['message'] = response

        if not st.session_state.response['continue_chat']:
            voice = generate_voice(st.session_state.response['message'])
            st.session_state.assistant.append(voice)
            
            st.session_state.end = True
            st.rerun()

        voice = generate_voice(st.session_state.response['message'])
        st.session_state.assistant.append(voice)

        st.session_state.task.prompt.append({"role": "assistant", "content": st.session_state.response['message']})

        st.session_state.turn = False
        st.rerun()
    else:
        st.session_state.audio = st.audio_input("Record your message", key=len(st.session_state.user))

        if st.session_state.audio:
            
            st.session_state.user.append(st.session_state.audio.read())
            
            transcription = get_trascription(st.session_state.user[-1])
            st.session_state.task.prompt.append({"role": "user", "content": transcription})

            st.session_state.turn = True
            st.session_state.audio = None

            st.rerun()

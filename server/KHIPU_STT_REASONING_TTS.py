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

from server.prompts.user_call_no_tools import NAME_CHECK
from server.prompts.evaluation import EVALUATION

st.set_page_config(
    page_title="KIPUH - STT, Reasoning, TTS",
    layout="centered",
    initial_sidebar_state="auto"
)


# FUNCTIONS

def evaluate_assistant_output(conversation: list, target_name: str):
    # agent = Agent(
    #     model="gpt-4.5-preview", 
    #     model_type="chat",
    #     provider="openai",
    #     price={'input': 75.00, 'output': 150.00}
    # )

    agent = Agent(
        model="gpt-4o",
        model_type="chat",
    )    

    task = Task(
        user=EVALUATION,
        agent=agent,
        simple_response=True
    )

    response = task.run({"last_name": target_name, "conversation": conversation})
    return response

def save_evaluation_to_disk(evaluation: str, language: str):

    file_path = f"server/assets/evaluation/{language}.json"
    directory = os.path.dirname(file_path)
    os.makedirs(directory, exist_ok=True)

    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            data = json.load(file)
    else:
        data = []

    evaluation_json = json.loads(evaluation.replace("```json\n", "").replace("```", ""))
    evaluation_json['name'] = st.session_state.name
    data.append(evaluation_json)

    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)


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

    directory = os.path.dirname(file_path)
    os.makedirs(directory, exist_ok=True)

    audio.export(file_path, format="wav")

def save_prompt_to_disk(prompt: dict | list, file_path: str):

    directory = os.path.dirname(file_path)
    os.makedirs(directory, exist_ok=True)

    with open(file_path, "w") as file:
        json.dump(prompt, file)

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

names = [
    "Samuel Baptista",
    "Nacho Orlando",
    "Felipe Gouveia",
    "Samuel Heinrichs",
    "Nati Vallejo",
    "Martin Bouza",
]

languages = [
    "Portuguese",
    "Spanish",
    "English",
    "German",
    "French",
    "Italian",
]

cols = st.columns(2)

with cols[0]:
    name = st.selectbox("Select a name to test the tool.", names)

with cols[1]:
    language = st.selectbox("Select the your native language.", languages)

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
        user=NAME_CHECK,
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

if 'language' not in st.session_state:
    st.session_state.country = None

cols = st.columns(2)

st.divider()
st.write("### Chat Transcription")

if st.session_state.task.prompt:
    for i, message in enumerate(st.session_state.task.prompt):
        if i == 0:
            continue

        with st.chat_message(message['role']):
            if message['role'] == "assistant":
                content = json.loads(message['content'])
                st.write(content['message'])
            else:
                st.write(message['content'])

if cols[1].button("Reset", use_container_width=True, type='primary'):
    for key in st.session_state:
        del st.session_state[key]

    st.rerun()

if cols[0].button("Run", use_container_width=True) or st.session_state.run:
    st.session_state.run = True

    st.session_state.name = name
    st.session_state.language = language

    st.divider()
    st.write("### Audio")
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

        file_name = st.session_state.name.replace(" ", "_")
        file_id = str(uuid.uuid4())

        save_audio_to_disk(
            full_audio, 
            f"server/assets/audios/{file_name}_{st.session_state.language}_{file_id}.wav"
        )

        save_prompt_to_disk(
            st.session_state.task.prompt[1:],
            f"server/assets/transcriptions/{file_name}_{st.session_state.language}_{file_id}.json"
        )

        st.write("### Evaluation")

        evaluation = evaluate_assistant_output(
            st.session_state.task.prompt[2:], 
            st.session_state.name.split(" ")[-1]
        )

        st.write(evaluation)
        save_evaluation_to_disk(evaluation, st.session_state.language)

        st.write("### End of the conversation")
        st.write("Thank you for participating in this demo.")
        
        st.stop()

    st.divider()

    if st.session_state.turn:

        context = {
            "user_data": {
                "name": st.session_state.name.split(" ")[0],
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

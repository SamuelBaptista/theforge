import os
import time
import json

import streamlit as st

from twilio.rest import Client

from openai import OpenAI
from pydantic import BaseModel

from repenseai.genai.agent import Agent
from repenseai.genai.tasks.api import Task

from difflib import SequenceMatcher

from prompts.user_call import instruction, template


st.set_page_config(
    page_title="Tool Usage Demo",
    layout="centered",
    initial_sidebar_state="auto"
)


# FUNCTIONS

def send_sms(text: str, to: str):

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        from_='+19787634376',
        body=text,
        to=to
    )

    return message

def calculate_similarity(text: str, country: str):
    similarity_scores = {}

    names = {
        "Brazil": ["Baptista", "Gouveia", "Souza", "Silva", "Santos"],
        "Argentina": ["Gonzalez", "Rodriguez", "Gomez", "Fernandez", "Lopez", "Matteoda"],
    }

    for name in names[country]:

        score = SequenceMatcher(None, text, name).ratio()
        similarity_scores[name] = score

    sorted_scores = dict(sorted(similarity_scores.items(), key=lambda item: item[1], reverse=True))
    return sorted_scores

def generate_voice(text: str):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    tts_response = client.audio.speech.create(
        model="tts-1-hd",
        voice="shimmer",
        input=text,
        response_format="wav",
        speed=1.0,
    )

    return tts_response.content

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
    st.markdown("""
  - Speed, accent, tone, and emotional inflection are fixed during voice generation (no real-time adjustments).   
  - Enables text editing, contextual analysis, and logic refinement between transcription and LLM steps.  
  - Allows error correction, fact-checking, or adding structured data (e.g., translations, summaries).  
  - Sequential processing introduces delays but supports complex, layered workflows.  
  - Ideal for content-heavy tasks requiring reasoning (e.g., customer service analysis, report generation).    
  - **Transcription System**: Prioritizes reasoning and content manipulation at the cost of audio customization.  
  """)

with cols[1]:
    st.image("server/assets/tool_usage.png", width=300)

# PAGE

if "task" not in st.session_state:

    class LLMResponse(BaseModel):
        message: str
        continue_chat: bool  

    agent = Agent(
        model="gpt-4o", 
        model_type="chat", 
        tools=[send_sms, calculate_similarity],
        # json_mode=True,
        # json_schema=LLMResponse,
    )

    task = Task(
        instruction=instruction,
        prompt_template=template,
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


cases = [
    {
        "user_data": {
            "name": "Samuel",
            "phone": "+5519999872145",
            "email": "s.johnson@email.com",
            "dob": "1988-11-13",
            "country": "Brazil"
        },
        'missing_data': "last name"
    },
    {
        "user_data": {
            "name": "Ramiro",
            "phone": "+5519999872145",
            "email": "r.mat@gmail.com",
            "dob": "1988-11-13",
            "country": "Argentina"
        },
        'missing_data': "last name"
    },
]

index = st.selectbox(
    "Select a case",
    [
        f"{i+1} - {case['user_data']['name']}" 
        for i, case in enumerate(cases)
    ]
)

selected_case = cases[int(index.split(" - ")[0]) - 1]

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

if cols[0].button("Run", use_container_width=True) or st.session_state.run:
    st.session_state.run = True

    st.divider()

    if st.session_state.assistant and not st.session_state.turn:
        with st.chat_message("assistant"):
            st.audio(st.session_state.assistant[-1], autoplay=True)    

    if st.session_state.end:
        with st.chat_message("assistant"):
            st.audio(st.session_state.assistant[-1], autoplay=True)
            
        time.sleep(12)

        st.write("### End of the conversation")
        st.write("Thank you for participating in this demo.")
        
        st.stop()

    st.divider()

    if st.session_state.turn:

        response = st.session_state.task.run(selected_case)
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
            
            st.session_state.user.append(st.session_state.audio)
            
            transcription = get_trascription(st.session_state.audio.read())
            st.session_state.task.prompt.append({"role": "user", "content": transcription})

            st.session_state.turn = True
            st.session_state.audio = None

            st.rerun()

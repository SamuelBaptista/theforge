import os
import json
import base64
import asyncio
import websockets

from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.websockets import WebSocketDisconnect

from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect

from prompt import INSTRUCTIONS

from dotenv import load_dotenv
load_dotenv()


# Config

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
PHONE_NUMBER_FROM = os.getenv('PHONE_NUMBER_FROM')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DOMAIN = os.getenv('DOMAIN', 'localhost')
PORT = int(os.getenv('PORT', 8000))

VOICE = 'alloy' # alloy, ash, ballad, coral, echo, sage, shimmer and verse

LOG_EVENT_TYPES = [
    'error', 'response.content.done', 'rate_limits.updated', 'response.done',
    'input_audio_buffer.committed', 'input_audio_buffer.speech_stopped',
    'input_audio_buffer.speech_started', 'session.created'
]

# FUNCTIONS

# async def setup_listener():
#     listen = f"localhost:{PORT}"
#     token = os.getenv("NGROK_AUTH_TOKEN")

#     session = await ngrok.SessionBuilder().authtoken(token).connect()

#     listener = await (
#         session.http_endpoint()
#         .domain(DOMAIN)
#         .listen()
#     )

#     listener.forward(listen)

async def send_initial_conversation_item(openai_ws):
    """Send initial conversation so AI talks first."""
    initial_conversation_item = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": "Hi"
                }
            ]
        }
    }
    await openai_ws.send(json.dumps(initial_conversation_item))
    await openai_ws.send(json.dumps({"type": "response.create"}))

async def initialize_session(openai_ws):
    """Control initial session with OpenAI."""
    session_update = {
        "type": "session.update",
        "session": {
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "turn_detection": {"type": "server_vad"},
            "voice": VOICE,
            "instructions": INSTRUCTIONS,
            "temperature": 0.6,
        }
    }
    print('Sending session update:', json.dumps(session_update))
    await openai_ws.send(json.dumps(session_update))
    await send_initial_conversation_item(openai_ws)

# API

app = FastAPI()
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

@app.get('/', response_class=JSONResponse)
async def index_page():
    return {"message": "Twilio Media Stream Server is running!"}

@app.api_route("/make-call", methods=["POST"], response_class=JSONResponse)
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""

    """Make an outbound call."""

    request_json = await request.json()
    phone_number_to_call = request_json.get("phone_number_to_call")

    if not phone_number_to_call:
        return {'erro': "Please provide a phone_number_to_call in the request body."}

    outbound_twiml = (
        f'<?xml version="1.0" encoding="UTF-8"?>'
        f'<Response><Connect><Stream url="wss://{DOMAIN}/media-stream" /></Connect></Response>'
    )

    call = client.calls.create(
        from_=PHONE_NUMBER_FROM,
        to=phone_number_to_call,
        twiml=outbound_twiml
    )

    return {"message": f"Call to {phone_number_to_call} initiated.", "call_sid": call.sid}

@app.api_route("/incoming-call", methods=["GET", "POST"])
async def handle_incoming_call(request: Request):
    """Handle incoming call and return TwiML response to connect to Media Stream."""

    response = VoiceResponse()

    # <Say> punctuation to improve text-to-speech flow
    response.say(
        "Please wait while we connect your call to the A. I. voice assistant"
        "powered by Twilio and the Open-A.I. Realtime API"
    )

    response.pause(length=1)
    response.say("O.K. you can start talking!")

    host = request.url.hostname

    connect = Connect()
    connect.stream(url=f'wss://{host}/media-stream')

    response.append(connect)

    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket('/media-stream')
async def handle_media_stream(websocket: WebSocket):
    """Handle WebSocket connections between Twilio and OpenAI."""
    print("Client connected")
    await websocket.accept()

    async with websockets.connect(
        'wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview',
        additional_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1"
        }
    ) as openai_ws:
        await initialize_session(openai_ws)
        stream_sid = None
        transcript = []

        async def receive_from_twilio():
            """Receive audio data from Twilio and send it to the OpenAI Realtime API."""
            nonlocal stream_sid
            nonlocal transcript

            try:
                async for message in websocket.iter_text():
                    data = json.loads(message)
                    if data['event'] == 'media':
                        audio_append = {
                            "type": "input_audio_buffer.append",
                            "audio": data['media']['payload']
                        }
                        await openai_ws.send(json.dumps(audio_append))
                    elif data['event'] == 'start':
                        stream_sid = data['start']['streamSid']
                        print(f"Incoming stream has started {stream_sid}")
            except WebSocketDisconnect:
                print("Client disconnected.")
                if openai_ws.open:
                    await openai_ws.close()

                if stream_sid:
                        with open(f"realtime/data/transcript_{stream_sid}.txt", "w") as transcript_file:
                            transcript_file.write("\n".join(transcript))
                        print(f"Transcript saved to transcript_{stream_sid}.txt")                    

        async def send_to_twilio():
            """Receive events from the OpenAI Realtime API, send audio back to Twilio."""
            nonlocal stream_sid
            nonlocal transcript

            try:
                async for openai_message in openai_ws:
                    response = json.loads(openai_message)
                    if response['type'] in LOG_EVENT_TYPES:
                        print(f"Received event: {response['type']}", response)
                    if response['type'] == 'session.updated':
                        print("Session updated successfully:", response)
                    if response['type'] == 'response.done':
                        if response['response']['output']:
                            if response['response']['output'][0]['content']:
                                with open(f"realtime/data/transcript_{stream_sid}.txt", "a") as transcript_file:
                                    transcript_file.write("\n" + response['response']['output'][0]['content'][0]['transcript'])
                        print(f"Transcript saved to transcript_{stream_sid}.txt")                     
                    if response['type'] == 'response.audio.delta' and response.get('delta'):
                        try:
                            audio_payload = base64.b64encode(base64.b64decode(response['delta'])).decode('utf-8')
                            audio_delta = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {
                                    "payload": audio_payload
                                }
                            }
                            await websocket.send_json(audio_delta)
                        except Exception as e:
                            print(f"Error processing audio data: {e}")
            except Exception as e:
                print(f"Error in send_to_twilio: {e}")

        await asyncio.gather(receive_from_twilio(), send_to_twilio())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("call:app", host="localhost", port=PORT, workers=1)            
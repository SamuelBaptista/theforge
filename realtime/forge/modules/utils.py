import functools
import time
import json
import os
import asyncio
from datetime import datetime
from enum import Enum
import pyaudio
import tempfile
import subprocess

RUN_TIME_TABLE_LOG_JSON = "config/runtime_time_table.jsonl"

# Audio recording parameters
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 24000


class ModelName(str, Enum):
    state_of_the_art_model = "state_of_the_art_model"
    reasoning_model = "reasoning_model"
    sonnet_model = "sonnet_model"
    base_model = "base_model"
    fast_model = "fast_model"


# Mapping from enum options to model IDs
model_name_to_id = {
    ModelName.state_of_the_art_model: "o1-preview",
    ModelName.reasoning_model: "o1-mini",
    ModelName.sonnet_model: "claude-3-5-sonnet-20240620",
    ModelName.base_model: "gpt-4o-2024-08-06",
    ModelName.fast_model: "gpt-4o-mini",
}


def timeit_decorator(func):
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = round(end_time - start_time, 4)
        print(f"⏰ {func.__name__}() took {duration:.4f} seconds")

        jsonl_file = RUN_TIME_TABLE_LOG_JSON

        # Create new time record
        time_record = {
            "timestamp": datetime.now().isoformat(),
            "function": func.__name__,
            "duration": f"{duration:.4f}",
        }

        # Append the new record to the JSONL file
        with open(jsonl_file, "a") as file:
            json.dump(time_record, file)
            file.write("\n")

        return result

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = round(end_time - start_time, 4)
        print(f"⏰ {func.__name__}() took {duration:.4f} seconds")

        jsonl_file = RUN_TIME_TABLE_LOG_JSON

        # Create new time record
        time_record = {
            "timestamp": datetime.now().isoformat(),
            "function": func.__name__,
            "duration": f"{duration:.4f}",
        }

        # Append the new record to the JSONL file
        with open(jsonl_file, "a") as file:
            json.dump(time_record, file)
            file.write("\n")

        return result

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


# Load personalization settings
personalization_file = os.getenv("PERSONALIZATION_FILE", "./config/personalization.json")
with open(personalization_file, "r") as f:
    personalization = json.load(f)

ai_assistant_name = personalization.get("ai_assistant_name", "Assistant")
human_name = personalization.get("human_name", "User")
patient_name = personalization.get("patient_name", "Patient")
missing_data = personalization.get("missing_data", "missing data")


SESSION_INSTRUCTIONS = (
    f" Greet the patient: introduce yourself as {ai_assistant_name}, a health specialist."
     f" The patient name is {patient_name}"
     " Clearly state the patient's name, if you have it"
     " Ask the patient if they are available to answer some questions, if not, schedule a call back."  
     f" After he answers, Ask about the missing data: {missing_data}"
     "If the missing data are somehow related to names, you need to confirm the spelling."
    " Be patient about accent and spelling."
     " Speak each letter so the patient can confirm."  
     " When all information is confirmed, thank the patient for their time and end the call in a professional manner."
    f" After either confirm or not the {missing_data} tell him you are going to send a telegram bot to the user."
    f" If you can confirm the data, thanks the client politely, end the call and update the database with the new information, calling the function update_missing_data where the parameter missing data is a dict '{missing_data}:value confirmed from user'"
    " example update_missing_data({'patient_name': 'Felipe', 'ç': {'last_name': 'GOUVEIA'}} )"
    f"send the a telegram bot calling the function send_message_telegram_bot({patient_name},{missing_data}, success=true/false"
    "The success parameter will be decided by the user's response. IF we can confirm the data, success=True, else success=False"
)
PREFIX_PADDING_MS = 300
SILENCE_THRESHOLD = 0.5
SILENCE_DURATION_MS = 700


def match_pattern(pattern: str, key: str) -> bool:
    if pattern == "*":
        return True
    elif pattern.startswith("*") and pattern.endswith("*"):
        return pattern[1:-1] in key
    elif pattern.startswith("*"):
        return key.endswith(pattern[1:])
    elif pattern.endswith("*"):
        return key.startswith(pattern[:-1])
    else:
        return pattern == key



def run_uv_script(python_code: str) -> str:
    """
    Create a temporary Python script with the given code and run it using Astral UV.
    Returns the response from running the script.

    :param python_code: A Python code snippet as a string.
    :return: The response from running the script.
    """
    # Create a temporary file to hold the Python script
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        # Write the provided Python code to the temporary file
        temp_file.write(python_code.encode("utf-8"))
        temp_file_path = temp_file.name

    # Command to run the script using Astral UV
    uv_command = ["uv", "run", temp_file_path]

    try:
        # Run the uv command and capture the output
        result = subprocess.run(uv_command, capture_output=True, text=True)

        # Return the stdout and stderr from the uv execution
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)
    finally:
        # Cleanup: remove the temporary file after execution
        temp_file.close()

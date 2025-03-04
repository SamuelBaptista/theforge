import os
import random
import requests
from pydantic import BaseModel
from typing import Any
from datetime import datetime

from .llm import structured_output_prompt
from .memory_management import memory_manager
from .logging import log_info
from .utils import (
    timeit_decorator,
    personalization,
)
from .database import get_database_instance

@timeit_decorator
async def get_ingest_memory() -> dict:
    """
    Returns the current memory content using memory_manager.
    """
    memory_manager.load_memory()
    memory_content = memory_manager.get_xml_for_prompt(["*"])

    return {
        "ingested_content": memory_content,
        "message": "Memory ingested successfully",
        "success": True,
    }

@timeit_decorator
async def add_to_memory(key: str, value: Any) -> dict:
    """
    Adds a key-value pair to the memory using memory_manager.
    """
    success = memory_manager.upsert(key, value)
    if success:
        return {
            "message": f"Successfully added {key} to memory with value {value}",
            "success": True,
        }
    return {
        "message": f"Failed to add {key} to memory with value {value}",
        "status": "error"
    }

@timeit_decorator
async def get_current_time():
    return {"current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


@timeit_decorator
async def get_random_number():
    return {"random_number": random.randint(1, 100)}

from enum import Enum


class OutputFormat(str, Enum):
    CSV = ".csv"
    JSONL = ".jsonl"
    JSON_ARRAY = ".json"


class GenerateSQLResponse(BaseModel):
    file_name: str
    sql_query: str
    output_format: OutputFormat


@timeit_decorator
async def send_message_telegram_bot(first_name: str, missing_data: str, success=True) -> dict:
    """
    Send a message to a Telegram bot based on the user's prompt and chat_id.
    Simulate a SMS message to the user.
    """
    # Step 2: Send the message to the Telegram bot
    try:

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        telegram_url = os.getenv("TELEGRAM_URL", "https://api.telegram.org/bot")


        if not chat_id:
            return {"status": "error", "message": "No chat_id provided."}

        if not bot_token:
            return {"status": "error", "message": "No bot token provided."}

        if success:
            message = (f"Hello {first_name}, this is a message from Donna. We have confirmed your {missing_data}."
                       " Thank you for your time.")
        else:
            message = (f"Hello {first_name}, this is a message from Donna. We couldn't confirm your {missing_data}."
                       f" Please confirm it.")

        url = f"{telegram_url}{bot_token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message}

        log_info(f"📖 send_message_telegram_bot() URL: {url}" , style="bold magenta")

        response = requests.post(url, data=payload)

        log_info(f"📖 send_message_telegram_bot() Response: {response.json()}", style="bold magenta")

        memory_manager.upsert(f"{first_name}_telegram_response", response.json())
        memory_manager.save_memory()
        return {"success": True, "message": "Message sent to Telegram bot."}

    except Exception as e:
        print(f"Failed to send message: {e}")
        return {
            "status": "error",
            "message": f"Failed to send message to Telegram bot: {str(e)}",
        }


@timeit_decorator
async def update_patient_missing_data(missing_data: dict, patient_name: str) -> dict:
    """
    Update the patient's record in the 'patient' table with missing data.
    The missing_data parameter should be a JSON string containing key-value pairs
    representing the attributes to update. This function uses GPT to generate
    a valid SQL UPDATE query.
    """

    # Step 1: Load SQL dialect from personalization settings
    sql_dialect = personalization.get("sql_dialect")
    if not sql_dialect:
        return {"status": "error", "message": "No SQL dialect provided."}

    # Step 2: Load the corresponding database URL from environment variables
    database_url_env_var = f"{sql_dialect.upper()}_URL"
    database_url = os.getenv(database_url_env_var)
    if not database_url:
        return {
            "status": "error",
            "message": f"{database_url_env_var} environment variable not set."
        }
    # Step 3: Get the database instance and establish a connection
    try:
        database = get_database_instance(sql_dialect)
        database.connect(database_url)
    except Exception as e:
        return {"status": "error", "message": f"Failed to connect to database: {str(e)}"}

    # Step 4: Build a structured prompt for GPT to generate the SQL UPDATE query.
    #This is not necessary, we can right a plan SQL query, but for the sake of the example we are using GPT to generate the query.
    prompt_structure = f"""
    <purpose>
      Generate an SQL UPDATE query to update missing attributes for a patient record in the 'patient' table.
    </purpose>

    <instructions>
      <instruction>The patient's first name is '{patient_name}'.</instruction>
      <instruction>The missing data is provided as a dict containing column names and their new values.</instruction>
      <instruction>Generate a valid SQL UPDATE query that updates the record in the 'patient' table where column name = '{patient_name}' using the provided missing data.</instruction>
      <instruction>Respond exclusively with the SQL query.</instruction>
    </instructions>

    <missing-data>
      {missing_data}
    </missing-data>
    """

    response = structured_output_prompt(prompt_structure, GenerateSQLResponse)
    if not response:
        return {"status": "error", "message": "Failed to generate update query."}

    log_info(f" 📄 Generated SQL query: {response.sql_query}", style="bold magenta")

    try:
        database.execute_sql(response.sql_query)
    except Exception as e:
        return {"status": "error", "message": f"Failed to execute update query: {str(e)}"}
    finally:
        database.disconnect()

    return {
        "success": True,
        "message": f"Patient record updated successfully."
    }


function_map = {
    "get_ingest_memory": get_ingest_memory,
    "add_to_memory": add_to_memory,
    "get_current_time": get_current_time,
    "get_random_number": get_random_number,
    "send_message_telegram_bot": send_message_telegram_bot,
    "update_patient_missing_data": update_patient_missing_data,
}

tools = [
    {
        "type": "function",
        "name": "update_patient_missing_data",
        "description": "Update the patient's record in the 'PATIENT' table after confirming the missing data.",
        "parameters": {
            "type": "object",
            "properties": {
                "missing_data": {
                    "type": "object",
                    "description": "The missing data (json representation) to update in the patient's record.",
                },
                "patient_name": {
                    "type": "string",
                    "description": "The patient's name to update the record for. On the table is represented by the 'name' column.",
                },
            },
            "required": ["missing_data", "patient_name"],
        },
    },
    {
        "type": "function",
        "name": "send_message_telegram_bot",
        "description": "Send a message to the Telegram bot either confirming or requesting confirmation of the missing data.",
        "parameters": {
            "type": "object",
            "properties": {
                "first_name": {
                    "type": "string",
                    "description": "The user/patient name to be used in the message.",
                },
                "missing_data": {
                    "type": "string",
                    "description": "The missing data that the user/patient needs to confirm or that has been confirmed.",
                }
            },
            "required": ["first_name", "missing_data"],
        }
    },
]

# POC Python Realtime API o1 assistant


## Setup
- [Install uv](https://docs.astral.sh/uv/), 
- Setup environment `cp .env.sample .env` add your `OPENAI_API_KEY`
- Update `personalization.json` to fit your setup
- Install dependencies `uv sync`
- Run the realtime assistant `uv run forge ` or `uv run forge  --prompts "Hello, how are you?"`

## Configurations
We decided to create a integration with telegram because its easy to use, we can send messages to the user in real time and its FREE!

For now, those values are hard-code for the POC, but we can change it to a configuration file in the future.

More informations on how to get the chat_id and the bot token, see [this link](https://gist.github.com/nafiesl/4ad622f344cd1dc3bb1ecbe468ff9f8a#get-chat-id-for-a-private-chat)

```python
```shell
# Telegram Bot configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
TELEGRAM_URL=https://api.telegram.org/bot

# Database configuration (example for SQLite, PostgreSQL, etc.)
SQLITE_URL=your_sqlite_database_url
POSTGRES_URL=your_postgres_database_url #not supported yet

# Personalization settings for SQL dialect
SQL_DIALECT=sqlite   # or 'postgres' not supported 
```
## Assistant Tools
> See [TOOLS.md](src/real_time_api_async/TOOLS.md) for a detailed list of available tools and their descriptions.

## Personalization

You can customize the behavior of the assistant by modifying the `personalization.json` file. Here are the available options:

- `ai_assistant_name`: The name of the AI assistant.
- `patient_name`: The name of the human user.
- `sql_dialect`: The SQL dialect to use for database operations. Supported options are:
  - `sqlite`: For SQLite databases
  - `postgres`: For PostgreSQL databases (untested)
- `system_message_suffix`: A string that will be appended to the end of the system instructions for the AI assistant.

Example `personalization.json`:

```json
{
  "ai_assistant_name": "Ada",
  "sql_dialect": "sqlite",
  "patient_name": "John Doe",
  "missing_data": [
    "last_name"
  ],
  "system_message_suffix": "Always be helpful and concise in your responses."
}
```

The `system_message_suffix` allows you to add custom instructions or personality traits to open AI. This suffix will be appended to the end of the default system instructions, giving usmore control over how the model behaves and responds.


# Voice Recognition with AI – Prototypes Comparison

### Models

- **Whisper**: OpenAI's Speech-to-Text (STT) model.
- **TTS**: OpenAI's Text-to-Speech model.
- **VAD**: Voice Activity Detection model.
- **GPT-4o**: OpenAI's Generative Pre-trained Transformer 4 model.
- **Real-Time API**: Custom API for real-time voice processing.

This application uses Streamlit, the OpenAI API, and Python to create an interactive voice recognition system. The workflow is simple: the user speaks, the system converts speech to text via an API, processes the text with AI, and then converts the response back to speech. 

For our proof-of-concept (POC), we developed three distinct prototypes:

1. **Streamlit with Speech-to-Text and Text-to-Speech with OpenAI**  
2. **Real Streaming with Twill (Twilio)**  
3. **Real Time API with Functions**

Below you'll find a comparison of these prototypes along with their respective pros and cons, as well as a Mermaid diagram visualizing the workflow.

---

# **Prototype Comparisons**

| Feature | Streamlit + OpenAI STT/TTS | Real Streaming (Twilio) | Real-Time API + Functions |
|---------|----------------------------|-------------------------|---------------------------|
| **Pros** | Fast development, easy deployment, simple OpenAI integration | True real-time, scalable, built-in telephony support | High flexibility, real-time, scalable, microservice integration |
| **Cons** | Not real-time, limited scaling, UI constraints | High costs (Twilio & OpenAI), vendor lock-in, complex integration | Expensive, high implementation effort, API orchestration needed |
| **Real-Time Performance** | ❌ No real streaming | ✅ Optimized for live streaming | ✅ Can be optimized |
| **Scalability** | ⚠️ Limited for large user loads | ✅ Twilio's infra scales well | ✅ Can scale horizontally |
| **Customization** | ❌ Limited UI control | ⚠️ Twilio-dependent features | ✅ Fully customizable |
| **Cost Efficiency** | ✅ Low infra cost (OpenAI API only) | ❌ Twilio charges per minute & OpenAI API costs | ❌ High infra & API costs |

---

## **1️⃣ Streamlit with OpenAI (Whisper & TTS)**
**Overview**: Uses OpenAI’s **Whisper (Speech-to-Text)** and **TTS (Text-to-Speech)** models in a Streamlit web app for quick prototyping.

### ✅ **Pros**:
- **Fast Development**: No need for frontend/backend setup.  
- **Easy Integration**: Works seamlessly with OpenAI's APIs.  
- **Low Infra Costs**: Only pays for API usage.  

### ❌ **Cons**:
- **No Real-Time Processing**: Whisper is batch-based, causing delays.  
- **Scalability Issues**: UI and backend are not designed for high user loads.  
- **Limited UI Customization**: Streamlit lacks flexibility.  

---

## **2️⃣ Real Streaming with Twilio**
**Overview**: Uses **Twilio’s real-time streaming** to capture voice input, process it with OpenAI’s **Whisper (STT)**, and generate responses using OpenAI’s **TTS**.

### ✅ **Pros**:
- **True Real-Time**: No latency between user input and AI response.  
- **Telephony-Ready**: Ideal for voice-driven applications (e.g., call centers).  
- **Reliable Scaling**: Twilio’s infrastructure ensures uptime.  

### ❌ **Cons**:
- **High Cost**: Twilio charges **per streaming minute**, plus OpenAI API fees.  
- **Vendor Lock-In**: Dependent on Twilio’s ecosystem.  
- **Understanding User Input is Hard**: Streaming ASR (Whisper) struggles with accents, noise, and interruptions.  

---

## **3️⃣ Real-Time API with Functions**
**Overview**: A **custom API** that handles voice input, calls AI functions (OpenAI or custom), and returns **real-time responses**.

### ✅ **Pros**:
- **Customizable & Flexible**: Can be adapted for any use case.  
- **Optimized for Performance**: Real-time responses with efficient processing.  
- **Scalable**: Can be horizontally scaled based on demand.  
- **VAD** enables **natural** and **seamless** voice-based interactions.
- **Function Calling** enhances **AI utility** with **real-world actions**.
- **Built in prompt for accent and noise handling**.

### ❌ **Cons**:
- **High Development Complexity**: Requires backend expertise.  
- **Infrastructure Costs**: Hosting, databases, and scaling require investment.  
- **Difficult to Implement**: Function orchestration, error handling, and latency optimizations are complex.  

---

# **🔹 Final Thoughts**
- **Streamlit + OpenAI** → Best for POCs and **non-real-time prototypes**.  
- **Twilio Streaming** → Ideal for **real-time voice applications** but **expensive**.  
- **Custom API + Functions** → Best for **full control and scalability**, but requires **heavy engineering effort**.  



---
### CLI Text Prompts
You can also pass text prompts to the assistant via the CLI.
Use '|' to separate prompts to chain commands.

- `uv run forge  --prompts "Hello, how are you?"`

## Code Breakdown

### Code Organization
The codebase is organized within the `src/realtime_api_async` directory. The application is modularized, with core functionality divided into separate Python modules located in the `modules/` directory.

### Important Files and Directories
- **`main.py`**: This is the entry point of the application. It sets up the WebSocket connection, handles audio input/output, and manages the interaction between the user and the AI assistant.
- **`modules/` Directory**: Contains various modules handling different functionalities of the assistant:
  - `audio.py`: Handles audio playback, including adding silence padding to prevent audio clipping.
  - `async_microphone.py`: Manages asynchronous audio input from the microphone.
  - `database.py`: Provides database interfaces for different SQL dialects (e.g., SQLite, DuckDB, PostgreSQL) and executes SQL queries.
  - `llm.py`: Interfaces with language models, including functions for structured output parsing and chat prompts.
  - `logging.py`: Configures logging for the application using Rich for formatted and colorful logs.
  - `memory_management.py`: Manages the assistant's memory with operations to create, read, update, and delete memory entries.
  - `tools.py`: Contains definitions of tools and functions that the assistant can use to perform various actions.
  - `utils.py`: Provides utility functions used across the application, such as timing decorators, model enumerations, audio configurations, and helper methods.
- **`active_memory.json`**: Stores the assistant's active memory state, allowing it to persist information between interactions.
- **`personalization.json`**: Contains configuration settings used to personalize the assistant's behavior.
- **`db/` Directory**: Holds mock database files and SQL scripts for testing database functionalities.


### Tools Framework
Tools are functions defined in `modules/tools.py` that extend the assistant's capabilities. These tools are mapped in `function_map` and are available for the assistant to perform actions based on user requests. The assistant uses these tools to execute specific tasks, enhancing its functionality and allowing for dynamic interactions.


## Mock Database (sqlite and duckdb)
- Reset sqlite `rm db/mock_sqlite.db && sqlite3 db/mock_sqlite.db < db/mock_data_for_sqlite.sql`

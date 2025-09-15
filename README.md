# Proyecto1_Redes_Cliente

Author:

Nelson García Bravatti 

---

Report link:

```
https://uvggt-my.sharepoint.com/:w:/g/personal/gar22434_uvg_edu_gt/EaMQISoJgS1Mm7JBX-p2mKUBtN2guzFOMrZWtCecORYKxg?e=ngm8fN
```


---

# MCP Football Client

Dark-themed chat client (FastAPI + Streamlit) that talks to an MCP server (via the MCP protocol over stdio) and to an LLM (Claude) to answer questions and call tools like **`best_play`** and **`player_performance`** on StatsBomb open data.

> **Repo layout (client)**
>
> ```
> back-end/
>   main.py           # FastAPI app (spawns/connects to MCP server)
>   client.py         # MCP client session + tool orchestration with Claude
>   logs.py           # Logging to console/file
>   .env              # Runtime configuration (see below)
> front-end/
>   main.py           # Streamlit UI
>   chatbot.py        # UI logic (chat, tool/result rendering)
>   logs.py
> .streamlit/config.toml  # Dark/blue theme
> README.md
> pyproject.toml | requirements.txt
> ```

---

## Features

- 🔌 **MCP client** (stdio transport) to connect to a local MCP server.
- 🤖 **LLM tool use** (Claude): the assistant decides when to call MCP tools.
- 🧰 **Tool discovery**: `/tools` endpoint lists all server tools.
- 💬 **Chat UI** (Streamlit): dark/blue theme, tool results as expandable JSON.
- 📦 **Conversation logging**: stored as JSON files under `conversations/`.
- 🛡️ **CORS enabled** for local development.

---

## Prerequisites

- **Python 3.11+**
- An **MCP server** checked out locally (e.g., your `Proyecto1_Redes_MCP/server.py`)
- An **Anthropic API key** for Claude:
  - Set `ANTHROPIC_API_KEY` in environment or `.env`

> The MCP server must have its own dependencies installed (e.g., `socceraction`, `statsbombpy`).  
> The client and server can live in different virtual environments.

---

## Installation

You can use **uv** (recommended) or **pip**.

### Using `uv`

```bash
# From the client repository root
uv venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
# or
uv pip install -e .
```

### Using pip

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
# or
pip install -e .
```

---

## Configuration

```
Create back-end/.env (the app loads it on startup):

# Absolute path to your MCP server script
SERVER_SCRIPT_PATH=/absolute/path/to/Proyecto1_Redes_MCP/server.py

# Claude API key
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx

# (Optional) If your client supports choosing a specific Python for the server,
# set the interpreter that has the server's dependencies installed:
# SERVER_PYTHON=/absolute/path/to/Proyecto1_Redes_MCP/.venv/bin/python
```

---

## Running

1) Start the client back-end (FastAPI)

From back-end/:

```bash
source ../.venv/bin/activate   # or your env
uvicorn main:app --reload
```

You should see:

INFO:     Uvicorn running on http://127.0.0.1:8000

On startup the back-end will:

Spawn the MCP server via stdio (using SERVER_SCRIPT_PATH),

Initialize the MCP session,

Fetch and cache the server’s tools.

2) Start the client front-end (Streamlit)

From the repository root (or front-end/):

```bash
streamlit run front-end/main.py
```

Open the provided URL (typically http://localhost:8501).

---

## Usage

Chat via UI

Open the Streamlit app.

The sidebar shows the API URL and discovered tools (pills).

Type a question like:

“What was the best play (xT) for match 3895302?”

“Show player performance for match 3753974.”

When Claude calls a tool, you’ll see an expandable JSON card with the tool result.

##### Endpoints (Back-end)

GET /tools – returns tools exposed by the MCP server (name, description, input schema).

POST /query – sends a chat message to Claude; if the model decides to use a tool, the server calls it via MCP and returns the full message history.

POST /tool – (optional) call a specific tool by name with JSON args if your client.py exposes call_tool.

---

## Requirements

Typical client dependencies (see requirements.txt):

- fastapi, uvicorn

- httpx

- streamlit

- pydantic, pydantic-settings, python-dotenv

- mcp (client)

- anthropic

The MCP server has its own pyproject.toml/requirements.txt and must be installed separately.

---

## License

This project is for academic/educational use. Check the licenses of StatsBomb Open Data, Anthropic, and any other third-party libraries before redistribution.
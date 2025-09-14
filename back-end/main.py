from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
from contextlib import asynccontextmanager
from client import MCPClient
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    server_script_path: str = ""

settings = Settings()

async def lifespan():
    """
    Manage cleint startup and shutdown
    """

    #Startup
    client = MCPClient()

    try:
        connected = await client.connect_to_server(settings.server_script_path)
        if not connected:
            raise Exception("Failed to connect to server")
        app.state.client = client
        yield
    except Exception as e:
        raise Exception(f"Failed to connect to server: {str(e)}")
    finally:
        # Shutdown
        await client.cleanup()

app = FastAPI(title="MCP Chatbot Redes", lifespan=lifespan)
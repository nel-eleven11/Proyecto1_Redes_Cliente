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


@asynccontextmanager
async def lifespan():
    """
    Manage client startup and shutdown
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class QueryRequest(BaseModel):
    query: str

class Message(BaseModel):
    role: str
    content: Any

class ToolCall(BaseModel):
    name: str
    args: Dict[str, Any]


async def process_query(request: ):
    """
    Process a query and return the response
    """
    try:
        messages = []
        messages = await app.state.client.process_query(request.query)
        
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
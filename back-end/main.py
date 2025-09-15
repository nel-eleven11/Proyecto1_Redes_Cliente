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
    server_script_path: str = "/home/nelson/Documents/Uvg/Redes/Proyecto1_Redes_MCP/server.py"
    server_project_dir: str = "/home/nelson/Documents/Uvg/Redes/Proyecto1_Redes_MCP"

    #server_script_path: str = "/home/nelson/Documents/Uvg/Redes/Proyecto1_MCP_Servers/git-server/server.py"
    #server_project_dir: str = "/home/nelson/Documents/Uvg/Redes/Proyecto1_MCP_Servers/git-server"

    server_remote_url: str = "http://127.0.0.1:8080/mcp"

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage client startup and shutdown
    """

    #Startup
    client = MCPClient()

    try:
        connected = await client.connect_to_server(
            settings.server_script_path,
            server_cwd=settings.server_project_dir,
        )
        if not connected:
            raise Exception("Failed to connect to server")
        app.state.client = client
        yield
    except Exception as e:
        raise Exception(f"Failed to connect to server: {str(e)}")
    finally:
        # Shutdown
        await client.cleanup()

@asynccontextmanager
async def lifespan_remote(app: FastAPI):
    """
    Manage client startup and shutdown (REMOTE HTTP)
    """
    #Startup
    client = MCPClient()
    try:
        ok = await client.connect_to_remote_server(settings.server_remote_url)
        if not ok:
            raise Exception("Failed to connect to remote server")
        app.state.client = client
        yield
    except Exception as e:
        raise Exception(f"Failed to connect to remote server: {str(e)}")
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

@app.post("/query")
async def process_query(request: QueryRequest):
    """
    Process a query and return the response
    """
    try:
        messages = []
        messages = await app.state.client.process_query(request.query)
        
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools")
async def get_available_tools():
    """
    Get list of available tools from the server
    """
    try:
        tools = await app.state.client.get_mcp_tools()
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in tools
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tool")
async def call_tool(tool_call: ToolCall):
    """
    Call a specific tool from the server
    """
    try:
        result = await app.state.client.call_tool(tool_call.name, tool_call.args)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
from typing import Optional
from contextlib import AsyncExitStack
import traceback
from logs import logger
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from datetime import datetime
import json
import os

from anthropic import Anthropic
from anthropic.types import Message


class MCPClient: 
    """
    MCP Cliente class, comunicates with llm and mcp-servers
    """
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.llm = Anthropic()
        self.tools = []
        self.messages = []
        self.logger = logger
        
    # Connect to the mcp server
    async def connect_to_server(self, server_script_path: str):
        """
        Connects to an MCP server

        """

        # Validate server python script
        is_python = server_script_path.endswith(".py")
        if not (is_python):
            raise ValueError("Server script must be a .py file")

        server_params = StdioServerParameters(
            command="python", args=[server_script_path], env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        # Start session with server    
        await self.session.initialize()
        mcp_tools = await self.get_mcp_tools()
        self.tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema,
            }
            for tool in mcp_tools
        ]

        return True
        
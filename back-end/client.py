from typing import Optional
from contextlib import AsyncExitStack
import traceback
from utils.logger import logger
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
        
    #conectar con mcp server

    # llamar tools

    # conseguir tools            
from typing import Optional
from contextlib import AsyncExitStack
import traceback
from logs import logger
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from datetime import datetime
import json
import os
from pathlib import Path
from fastmcp import Client as FastMCPClient

from anthropic import Anthropic
from anthropic.types import Message


class MCPClient: 
    """
    MCP Cliente class, comunicates with llm and mcp-servers
    """
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None          
        self.remote_client: Optional[FastMCPClient] = None   
        self.exit_stack = AsyncExitStack()
        self.llm = Anthropic()
        self.tools = []
        self.messages = []
        self.logger = logger
        
    # Connect to a local MCP server via stdio 
    async def connect_to_server(self, server_script_path: str, server_cwd: Optional[str] = None):
        """
        Connects to an MCP server over stdio (local process).
        """

        # Validate server python script
        is_python = server_script_path.endswith(".py")
        if not (is_python):
            raise ValueError("Server script must be a .py file")

        cwd = server_cwd or Path(server_script_path).parent.as_posix()

        self.logger.info(f"Starting MCP server with uv: uv run {server_script_path} (cwd={cwd})")

        server_params = StdioServerParameters(
            command="uv", 
            args=["run", server_script_path],
            env=os.environ.copy(),
            cwd=cwd,
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

    # Connect to a remote MCP server via HTTP 
    async def connect_to_remote_server(self, base_url: str):
        """
        Connects to a remote MCP server (HTTP) using FastMCP Client.
        """
        self.logger.info(f"Connecting to remote MCP server: {base_url}")

        # Open FastMCP HTTP client in the same exit_stack for unified cleanup
        self.remote_client = await self.exit_stack.enter_async_context(FastMCPClient(base_url))
               
        # Fetch and cache tools (same shape used by Anthropic tools param)
        mcp_tools = await self.get_mcp_tools()
        self.tools = [
            {
                "name": t.name,
                "description": getattr(t, "description", "") or "",
                "input_schema": getattr(t, "inputSchema", None) or getattr(t, "input_schema", None),
            }
            for t in mcp_tools
        ]

        self.logger.info("Connected to remote MCP server successfully.")
        return True

    async def call_tool(self, name: str, args: dict):
        """
        Helper the /tool endpoint expects
        """
        # Prefer remote if present
        if self.remote_client:
            return await self.remote_client.call_tool(name, args)

        if not self.session:
            raise RuntimeError("MCP session not initialized. Call connect_to_server or connect_to_remote_server first.")
        return await self.session.call_tool(name, args)

    async def get_mcp_tools(self):
        """
        Get the different tools from the server (remote or local)
        """
        try:
            self.logger.info("Requesting MCP tools from the server.")
            if self.remote_client:
                response = await self.remote_client.list_tools()
                return response
            else:
                response = await self.session.list_tools()
                if hasattr(response, "tools"):
                    return response.tools
                # Fallback
                if isinstance(response, list):
                    return response
            raise TypeError(f"Unexpected tools response type: {type(response)}")

        except Exception as e:
            self.logger.error(f"Failed to get MCP tools: {str(e)}")
            self.logger.debug(f"Error details: {traceback.format_exc()}")
            raise Exception(f"Failed to get tools: {str(e)}")

    
    async def cleanup(self):
        """
        Clean up resources
        """
        try:
            self.logger.info("Cleaning up resources")
            await self.exit_stack.aclose()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

    async def call_llm(self) -> Message:
        """
        Call the LLM with the given query
        """
        try:
            return self.llm.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=self.messages,
                tools=self.tools,
            )
        except Exception as e:
            self.logger.error(f"Failed to call LLM: {str(e)}")
            raise Exception(f"Failed to call LLM: {str(e)}")


    async def process_query(self, query: str):
        """
        Process a query using Claude and available tools, returning all messages at the end
        """
        try:
            #  Log first 100 chars of query
            self.logger.info(
                f"Processing new query: {query[:100]}..."
            )  

            # Add the initial user message
            user_message = {"role": "user", "content": query}
            self.messages.append(user_message)
            await self.log_conversation(self.messages)
            messages = [user_message]

            while True:
                self.logger.debug("Calling Claude API")
                response = await self.call_llm()

                # If it's a simple text response
                if response.content[0].type == "text" and len(response.content) == 1:
                    assistant_message = {
                        "role": "assistant",
                        "content": response.content[0].text,
                    }
                    self.messages.append(assistant_message)
                    await self.log_conversation(self.messages)
                    messages.append(assistant_message)
                    break

                # For more complex responses with tool calls
                assistant_message = {
                    "role": "assistant",
                    "content": response.to_dict()["content"],
                }
                self.messages.append(assistant_message)
                await self.log_conversation(self.messages)
                messages.append(assistant_message)

                for content in response.content:
                    if content.type == "text":
                        # Text content within a complex response
                        text_message = {"role": "assistant", "content": content.text}
                        await self.log_conversation(self.messages)
                        messages.append(text_message)
                    elif content.type == "tool_use":
                        tool_name = content.name
                        tool_args = content.input
                        tool_use_id = content.id

                        self.logger.info(
                            f"Executing tool: {tool_name} with args: {tool_args}"
                        )
                        try:
                            # route to local stdio or remote http automatically
                            result = await self.call_tool(tool_name, tool_args)
                            self.logger.info(f"Tool result: {result}")

                            if self.remote_client:
                                # Normalize contents -> Anthropic
                                anth_content = []
                                for item in (result.content or []):
                                    if getattr(item, "type", None) == "text" and getattr(item, "text", None) is not None:
                                        anth_content.append({"type": "text", "text": item.text})
                                    elif getattr(item, "type", None) == "json" and getattr(item, "json", None) is not None:
                                        anth_content.append({"type": "json", "json": item.json})
                                    else:
                                        anth_content.append({"type": "text", "text": str(getattr(item, "text", item))})

                                tool_result_message = {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "tool_result",
                                            "tool_use_id": tool_use_id,
                                            "content": anth_content,
                                        }
                                    ],
                                }
                            else:
                                # stdio local
                                tool_result_message = {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "tool_result",
                                            "tool_use_id": tool_use_id,
                                            "content": result.content,
                                        }
                                    ],
                                }
                            self.messages.append(tool_result_message)
                            await self.log_conversation(self.messages)
                            messages.append(tool_result_message)

                        except Exception as e:
                            error_msg = f"Tool execution failed: {str(e)}"
                            self.logger.error(error_msg)
                            tool_result_message = {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": tool_use_id,
                                        "content": [{"type": "text", "text": error_msg}],
                                    }
                                ],
                            }
                            self.messages.append(tool_result_message)
                            await self.log_conversation(self.messages)
                            messages.append(tool_result_message)
                            raise Exception(error_msg)

            return messages

        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            self.logger.debug(
                f"Query processing error details: {traceback.format_exc()}"
            )
            raise

    
    async def log_conversation(self, conversation: list):
        """
        Log the conversation to json file
        """

        # Create conversations directory if it doesn't exist
        os.makedirs("conversations", exist_ok=True)

        # Convert conversation to JSON-serializable format
        serializable_conversation = []
        for message in conversation:
            try:
                serializable_message = {
                    "role": message["role"],
                    "content": []
                }
                
                # Handle both string and list content
                if isinstance(message["content"], str):
                    serializable_message["content"] = message["content"]                  
                elif isinstance(message["content"], list):
                    for content_item in message["content"]:
                        if hasattr(content_item, 'to_dict'):
                            serializable_message["content"].append(content_item.to_dict())
                        elif hasattr(content_item, 'dict'):
                            serializable_message["content"].append(content_item.dict())
                        elif hasattr(content_item, 'model_dump'):
                            serializable_message["content"].append(content_item.model_dump())
                        else:
                            serializable_message["content"].append(content_item)
                
                serializable_conversation.append(serializable_message)
            except Exception as e:
                self.logger.error(f"Error processing message: {str(e)}")
                self.logger.debug(f"Message content: {message}")
                raise

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filepath = os.path.join("conversations", f"conversation_{timestamp}.json")
        
        try:
            with open(filepath, "w") as f:
                json.dump(serializable_conversation, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Error writing conversation to file: {str(e)}")
            self.logger.debug(f"Serializable conversation: {serializable_conversation}")
            raise


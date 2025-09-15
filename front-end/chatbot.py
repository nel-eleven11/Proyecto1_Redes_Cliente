import streamlit as st
import httpx
from typing import Dict, Any
import json


class Chatbot:
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.current_tool_call = {"name": None, "args": None}
        self.messages = st.session_state["messages"]

    def display_message(self, message: Dict[str, Any]):
        """
        Show formated messages
        """

        # display user message
        if message["role"] == "user" and type(message["content"]) == str:
            st.chat_message("user").markdown(message["content"])

        # display tool result
        if message["role"] == "user" and type(message["content"]) == list:
            for content in message["content"]:
                if content["type"] == "tool_result":
                    with st.chat_message("assistant"):
                        st.write(f"Called tool: {self.current_tool_call['name']}:")
                        st.json(
                            {
                                "name": self.current_tool_call["name"],
                                "args": self.current_tool_call["args"],
                                "content": json.loads(content["content"][0]["text"]),
                            },
                            expanded=False,
                        )

        # display ai message
        if message["role"] == "assistant" and type(message["content"]) == str:
            st.chat_message("assistant").markdown(message["content"])

        # store current ai tool use
        if message["role"] == "assistant" and type(message["content"]) == list:
            for content in message["content"]:
                # ai tool use
                if content["type"] == "tool_use":
                    self.current_tool_call = {
                        "name": content["name"],
                        "args": content["input"],
                    }

    async def get_tools(self):
        """
        Get the tools from the server
        """
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            response = await client.get(
                f"{self.api_url}/tools",
                headers={"Content-Type": "application/json"},
            )
            return response.json()

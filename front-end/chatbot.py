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
        Render a single message with nice chat bubbles and tool cards.
        """
        # User text
        if message["role"] == "user" and isinstance(message["content"], str):
            st.chat_message("user", avatar="🧑").markdown(message["content"])

        # Tool result (assistant reply to a tool call)
        if message["role"] == "user" and isinstance(message["content"], list):
            for content in message["content"]:
                if content.get("type") == "tool_result":
                    with st.chat_message("assistant", avatar="🤖"):
                        st.markdown(
                            f"**Tool executed:** `{self.current_tool_call['name']}`", help="Tool call result"
                        )
                        with st.expander("View result JSON", expanded=False):
                            st.json(
                                {
                                    "tool": self.current_tool_call["name"],
                                    "args": self.current_tool_call["args"],
                                    "content": json.loads(content["content"][0]["text"]),
                                }
                            )

        # Assistant text
        if message["role"] == "assistant" and isinstance(message["content"], str):
            st.chat_message("assistant", avatar="🤖").markdown(message["content"])

        # Assistant tool use (store current call so we can label the result)
        if message["role"] == "assistant" and isinstance(message["content"], list):
            for content in message["content"]:
                if content.get("type") == "tool_use":
                    self.current_tool_call = {
                        "name": content["name"],
                        "args": content["input"],
                    }

    async def get_tools(self):
        """
        Get the tools from the server
        """
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            resp = await client.get(f"{self.api_url}/tools", headers={"Content-Type": "application/json"})
            resp.raise_for_status()
            return resp.json()

    async def render(self):
        """
        Render entire UI (sidebar + chat area)
        """
        # Sidebar: status + tools
        with st.sidebar:
            st.subheader("Settings")
            st.write("API URL:", f"`{self.api_url}`")

            tools = []
            try:
                result = await self.get_tools()
                tools = result.get("tools", [])
                st.success("Connected to MCP Server", icon="✅")
            except Exception as e:
                st.error(f"Server connection failed\n\n{e}", icon="⚠️")

            st.subheader("Tools")
            if tools:
                pills = " ".join([f"<span class='tool-pill'>{t['name']}</span>" for t in tools])
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.caption("No tools available")

            st.markdown("---")
            if st.button("🧹 Clear chat", use_container_width=True):
                st.session_state["messages"] = []
                self.messages = []
                st.rerun()

        # Existing messages
        for msg in self.messages:
            self.display_message(msg)

        # New query
        query = st.chat_input("Type your question or ask me to run a tool…")
        if query:
            async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
                try:
                    resp = await client.post(
                        f"{self.api_url}/query",
                        json={"query": query},
                        headers={"Content-Type": "application/json"},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    messages = data.get("messages", [])
                    st.session_state["messages"] = messages
                    # Re-render freshly
                    for msg in st.session_state["messages"]:
                        self.display_message(msg)
                except Exception as e:
                    st.error(f"Frontend: Error processing query: {str(e)}")

import asyncio
import streamlit as st
from logs import logger
from chatbot import Chatbot


def _inject_css():
    # Global dark+blue styling
    st.markdown(
        """
        <style>
        /* App background with subtle radial gradient */
        .stApp {
            background: radial-gradient(120% 150% at -10% -20%, #0b1220 0%, #08101b 50%, #070d17 100%);
        }

        /* Sidebar gradient + divider */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0F1B2E 0%, #0B1220 100%);
            border-right: 1px solid rgba(255,255,255,0.08);
        }

        /* Headings */
        h1, h2, h3 { letter-spacing: .2px; }

        /* Header block */
        .app-header h1 {
            font-size: 1.8rem;
            margin-bottom: .25rem;
        }
        .app-header .subtle {
            color: #9bb3d1;
            font-size: 0.95rem;
        }

        /* Chat message cards */
        .stChatMessage {
            border-radius: 14px;
            padding: .5rem .75rem;
        }
        .stChatMessage[data-testid="stChatMessageUser"] {
            background: #081a2b;
            border: 1px solid rgba(112,160,255,0.18);
        }
        .stChatMessage[data-testid="stChatMessageAssistant"] {
            background: #0f2036;
            border: 1px solid rgba(112,160,255,0.12);
        }

        /* Chat input */
        div[data-testid="stChatInput"]>div>div {
            background:#0f1b2e;
            border:1px solid rgba(112,160,255,0.20);
            border-radius: 12px;
        }

        /* Tool "pills" */
        .tool-pill {
            display:inline-block;
            padding:.25rem .6rem;
            margin:.15rem .25rem .15rem 0;
            border-radius:999px;
            border:1px solid rgba(112,160,255,.35);
            background: rgba(51,102,204,.15);
            font-size:.85rem;
            white-space:nowrap;
        }

        /* JSON / code blocks */
        .stMarkdown pre, .stCodeBlock pre, code, pre {
            background:#0a1626 !important;
            border:1px solid rgba(112,160,255,.16) !important;
            border-radius:10px !important;
        }

        /* Subtle hr */
        hr { border-color: rgba(255,255,255,0.06); }
        </style>
        """,
        unsafe_allow_html=True,
    )


async def main():
    if "server_connected" not in st.session_state:
        st.session_state["server_connected"] = False
    if "tools" not in st.session_state:
        st.session_state["tools"] = []
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    st.set_page_config(
        page_title="MCP Chatbot Redes",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _inject_css()

    # Header
    st.markdown(
        """
        <div class="app-header">
            <h1>⚽ MCP Football Chat</h1>
            <div class="subtle">Ask questions, run tools, and explore StatsBomb data.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    API_URL = "http://127.0.0.1:8000"
    chatbot = Chatbot(API_URL)
    await chatbot.render()


if __name__ == "__main__":
    asyncio.run(main())

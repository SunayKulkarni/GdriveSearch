from __future__ import annotations

import logging
import os
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from backend.drive_tool import GoogleDriveSearchTool, get_raw_files

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a Google Drive file discovery assistant.\n"
    "Use Google Drive query syntax when searching:\n"
    "- name contains 'x'\n"
    "- mimeType = '...'\n"
    "- For images: mimeType contains 'image/'\n"
    "- For PDFs: mimeType = 'application/pdf'\n"
    "- fullText contains 'x'\n"
    "- modifiedTime > '2024-01-01T00:00:00'\n"
    "Always append: and trashed = false\n"
    "Call the google_drive_search tool once per user request with a single valid query.\n"
    "Do not generate long OR lists of mimeType values. Use a single mimeType or a single contains clause."
)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def _load_llm() -> Any:
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model="gpt-4o-mini", temperature=0)
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)
    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(model="llama-3.1-8b-instant", temperature=0)

    logger.warning("Unknown LLM_PROVIDER=%s, defaulting to gemini", provider)
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)


def _should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return "end"


def _build_messages(history: list[dict], message: str) -> list[BaseMessage]:
    messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]

    for item in history:
        role = str(item.get("role", "")).lower()
        content = str(item.get("content", ""))
        if not content:
            continue
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
        else:
            messages.append(HumanMessage(content=content))

    messages.append(HumanMessage(content=message))
    return messages


def _shortcut_query(message: str) -> str | None:
    normalized = message.strip().lower()
    if not normalized:
        return None

    if any(
        phrase in normalized
        for phrase in [
            "list all files",
            "list files",
            "show all files",
            "all files",
            "all the files",
            "list all the files",
            "list all files in",
            "list all the files in",
        ]
    ):
        return "trashed = false"

    if "find images" in normalized or "image files" in normalized:
        return "mimeType contains 'image/' and trashed = false"

    if "pdf" in normalized:
        return "mimeType = 'application/pdf' and trashed = false"

    return None


_APP = None


def _get_app():
    global _APP
    if _APP is not None:
        return _APP

    drive_tool = GoogleDriveSearchTool()
    llm = _load_llm()
    bound_llm = llm.bind_tools([drive_tool])

    def llm_node(state: AgentState) -> dict:
        response = bound_llm.invoke(state["messages"])
        return {"messages": [response]}

    tool_node = ToolNode([drive_tool])

    graph = StateGraph(AgentState)
    graph.add_node("llm", llm_node)
    graph.add_node("tools", tool_node)
    graph.add_edge("tools", "llm")
    graph.add_conditional_edges("llm", _should_continue, {"tools": "tools", "end": END})
    graph.set_entry_point("llm")

    _APP = graph.compile()
    return _APP


def run_agent(message: str, history: list[dict]) -> dict:
    try:
        shortcut = _shortcut_query(message)
        if shortcut:
            tool = GoogleDriveSearchTool()
            response_text = tool._run(shortcut, max_results=50)
            return {"response": response_text, "files": get_raw_files()}

        app = _get_app()
        messages = _build_messages(history, message)
        result = app.invoke({"messages": messages})

        response_text = ""
        tool_called = False
        for msg in result.get("messages", []):
            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                tool_called = True

        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage):
                response_text = msg.content or ""
                break

        files = get_raw_files() if tool_called else []
        return {"response": response_text, "files": files}
    except Exception as exc:
        logger.exception("Agent execution failed")
        return {"response": f"Error: {exc}", "files": []}

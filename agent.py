"""LangGraph ReAct agent — MCP servers start once and are reused across queries."""
import asyncio
import os
import queue
import sys
import threading
from pathlib import Path
from typing import Generator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

SERVERS_DIR = Path(__file__).parent / "servers"

SYSTEM_PROMPT = """You are an enterprise AI assistant with access to two tools:

1. Data Catalog (DuckDB) — tables: employees, projects, sales
   Use list_tables, describe_table, run_sql to answer data questions.

2. Vector Search (ChromaDB) — enterprise knowledge base
   Use semantic_search, list_documents for document retrieval.

Always use the tools to retrieve accurate data before answering.
Be concise and present numbers/results in a readable format."""

SERVER_CFG = {
    "catalog": {
        "command":   sys.executable,
        "args":      [str(SERVERS_DIR / "catalog_server.py")],
        "transport": "stdio",
    },
    "vector": {
        "command":   sys.executable,
        "args":      [str(SERVERS_DIR / "vector_server.py")],
        "transport": "stdio",
    },
}

# ── Persistent background event loop ──────────────────────────────────────────
# Shared across all Streamlit reruns so MCP subprocesses start only once.
_bg_loop: asyncio.AbstractEventLoop | None = None
_bg_thread: threading.Thread | None = None
_cached_tools: list | None = None


def _start_bg_loop():
    global _bg_loop
    _bg_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_bg_loop)
    _bg_loop.run_forever()


def _ensure_loop() -> asyncio.AbstractEventLoop:
    global _bg_loop, _bg_thread
    if _bg_thread is None or not _bg_thread.is_alive():
        _bg_thread = threading.Thread(target=_start_bg_loop, daemon=True)
        _bg_thread.start()
        while _bg_loop is None:
            import time; time.sleep(0.01)
    return _bg_loop


def _run(coro):
    """Submit a coroutine to the background loop and block until done."""
    return asyncio.run_coroutine_threadsafe(coro, _ensure_loop()).result()


# ── LLM factory ───────────────────────────────────────────────────────────────
def _make_llm(model: str):
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        from langchain_groq import ChatGroq
        return ChatGroq(model=model, temperature=0, api_key=groq_key)
    from langchain_ollama import ChatOllama
    return ChatOllama(model=model, temperature=0)


# ── Tool cache — MCP subprocesses start once ──────────────────────────────────
async def _init_tools():
    global _cached_tools
    if _cached_tools is not None:
        return _cached_tools
    from langchain_mcp_adapters.client import MultiServerMCPClient
    client = MultiServerMCPClient(SERVER_CFG)
    _cached_tools = await client.get_tools()
    return _cached_tools


def get_tools():
    return _run(_init_tools())


# ── Agent streaming ────────────────────────────────────────────────────────────
async def _stream_agent(question: str, model: str):
    from langgraph.prebuilt import create_react_agent

    tools  = await _init_tools()
    llm    = _make_llm(model)
    agent  = create_react_agent(llm, tools)

    messages     = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=question)]
    seen_calls   = set()
    seen_results = set()

    async for chunk in agent.astream({"messages": messages}, stream_mode="updates"):
        for _, node_data in chunk.items():
            for msg in node_data.get("messages", []):
                if isinstance(msg, AIMessage):
                    for tc in msg.tool_calls:
                        key = (tc["name"], str(sorted(tc["args"].items())))
                        if key not in seen_calls:
                            seen_calls.add(key)
                            yield {"type": "tool_call", "name": tc["name"], "args": tc["args"]}
                    if msg.content and not msg.tool_calls:
                        yield {"type": "answer", "content": msg.content}
                elif isinstance(msg, ToolMessage):
                    if msg.tool_call_id not in seen_results:
                        seen_results.add(msg.tool_call_id)
                        yield {"type": "tool_result", "tool": msg.name, "content": msg.content[:600]}


def run_agent(question: str, model: str = "llama3.2:3b") -> Generator[dict, None, None]:
    """Synchronous generator — safe to call from Streamlit."""
    out: queue.Queue = queue.Queue()

    async def producer():
        try:
            async for event in _stream_agent(question, model):
                out.put(event)
        except Exception as exc:
            out.put({"type": "error", "content": str(exc)})
        finally:
            out.put(None)

    asyncio.run_coroutine_threadsafe(producer(), _ensure_loop())

    while True:
        item = out.get()
        if item is None:
            break
        yield item

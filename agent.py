"""LangGraph ReAct agent — uses Groq (cloud) or Ollama (local) depending on env."""
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


def _make_llm(model: str):
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if groq_key:
        from langchain_groq import ChatGroq
        return ChatGroq(model=model, temperature=0, api_key=groq_key)
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model, temperature=0)


async def _stream_agent(question: str, model: str):
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langgraph.prebuilt import create_react_agent

    server_cfg = {
        "catalog": {
            "command": sys.executable,
            "args":    [str(SERVERS_DIR / "catalog_server.py")],
            "transport": "stdio",
        },
        "vector": {
            "command": sys.executable,
            "args":    [str(SERVERS_DIR / "vector_server.py")],
            "transport": "stdio",
        },
    }

    client = MultiServerMCPClient(server_cfg)
    tools  = await client.get_tools()
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
    """Synchronous generator wrapper — safe to call from Streamlit."""
    q: queue.Queue = queue.Queue()

    async def producer():
        try:
            async for event in _stream_agent(question, model):
                q.put(event)
        except Exception as exc:
            q.put({"type": "error", "content": str(exc)})
        finally:
            q.put(None)

    def thread_target():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(producer())
        loop.close()

    threading.Thread(target=thread_target, daemon=True).start()

    while True:
        item = q.get()
        if item is None:
            break
        yield item

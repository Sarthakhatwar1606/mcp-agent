# MCP Tool-Calling Agent

Enterprise AI agent using **MCP** for secure tool calling and governed data access — built entirely with free, open-source tools.

## Stack (100% free)

| Concept | Paid version | Free replacement |
|---|---|---|
| Agent framework | Databricks Agent Framework | **LangGraph** |
| Data catalog | Unity Catalog | **DuckDB** |
| Vector search | Databricks Vector Search | **ChromaDB** |
| LLM | OpenAI / Azure | **Ollama** (local) |
| Tool protocol | proprietary | **MCP** (open source) |

## Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Pull a local LLM
ollama pull llama3.2:3b

# 3. Seed sample data
python seed_data.py

# 4. Launch the app
streamlit run app.py
```

## Architecture

```
Streamlit UI
    └── agent.py  (LangGraph ReAct agent)
            ├── catalog_server.py  (MCP server → DuckDB)
            │     tools: list_tables · describe_table · run_sql
            └── vector_server.py   (MCP server → ChromaDB)
                  tools: semantic_search · list_documents · add_document
```

MCP servers run as **stdio subprocesses** — the agent spawns them, calls tools over stdin/stdout, and they shut down when the agent finishes. This is the MCP standard transport.

## Sample questions

- "What tables are in the data catalog?"
- "Show the top 3 highest paid employees"
- "What's our Q2 2024 total revenue by region?"
- "Find documents about security policy"
- "Which project has the largest budget and what's its status?"
- "Search for information about the AI recommendation engine"

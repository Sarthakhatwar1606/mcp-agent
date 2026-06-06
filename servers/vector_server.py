"""MCP server — ChromaDB vector/semantic search (Vector Search replacement, free)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import compat  # noqa: F401 — stubs broken protobuf modules before chromadb loads

import json

import chromadb
from mcp.server.fastmcp import FastMCP

CHROMA_PATH = str(Path(__file__).parent.parent / "data" / "chromadb")
COLLECTION  = "documents"
mcp = FastMCP("Vector Search")


def _col():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})


@mcp.tool()
def semantic_search(query: str, n_results: int = 5) -> str:
    """Search the enterprise knowledge base using natural language (semantic similarity)."""
    col = _col()
    count = col.count()
    if count == 0:
        return json.dumps({"results": [], "message": "Knowledge base is empty. Add documents first."})
    results = col.query(query_texts=[query], n_results=min(n_results, count))
    output = [
        {
            "id":       results["ids"][0][i],
            "score":    round(1 - results["distances"][0][i], 4),
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
        }
        for i in range(len(results["documents"][0]))
    ]
    return json.dumps(output, indent=2)


@mcp.tool()
def list_documents() -> str:
    """List all documents currently stored in the enterprise knowledge base."""
    col = _col()
    count = col.count()
    if count == 0:
        return json.dumps({"count": 0, "documents": []})
    all_docs = col.get()
    docs = [
        {
            "id":       all_docs["ids"][i],
            "preview":  all_docs["documents"][i][:120] + "…",
            "metadata": all_docs["metadatas"][i],
        }
        for i in range(len(all_docs["ids"]))
    ]
    return json.dumps({"count": count, "documents": docs}, indent=2)


@mcp.tool()
def add_document(doc_id: str, content: str, category: str = "general", source: str = "") -> str:
    """Add a new document to the enterprise knowledge base."""
    col = _col()
    col.add(documents=[content], ids=[doc_id], metadatas=[{"category": category, "source": source}])
    return json.dumps({"success": True, "id": doc_id, "total": col.count()})


if __name__ == "__main__":
    mcp.run(transport="stdio")

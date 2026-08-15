"""Three-layer Agent Memory System package.

Exports WorkingMemoryManager, EpisodicMemoryManager, LongTermMemoryManager, and
registers memory operations tools (recall_findings, search_memory, save_finding) with default_registry.
"""

import json
from typing import Optional, List, Dict, Any

from agent.tools.registry import default_registry
from agent.memory.working import WorkingMemoryManager
from agent.memory.longterm import LongTermMemoryManager, MemoryEntry
from agent.memory.episodic import EpisodicMemoryManager

# Global singleton memory manager instances
global_longterm_memory = LongTermMemoryManager()
global_episodic_memory = EpisodicMemoryManager(longterm_manager=global_longterm_memory)
global_working_memory = WorkingMemoryManager()


# ==============================================================================
# TOOL 1: save_finding
# ==============================================================================
@default_registry.tool(
    name="save_finding",
    description="Save a key financial research finding or disclosure into persistent memory for cross-session and episodic retrieval.",
    parameters_schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Key financial finding, metric, or disclosure narrative text to store."},
            "source": {"type": "string", "description": "Source identifier (e.g., 'sec_edgar_10k', 'earnings_transcript', 'agent_synthesis')."},
            "ticker": {"type": "string", "description": "Stock ticker symbol (e.g. JPM, AAPL)."},
            "filing_type": {"type": "string", "description": "Filing form type (e.g. '10-K', '10-Q')."}
        },
        "required": ["text"]
    }
)
def save_finding(text: str, source: str = "agent_synthesis", ticker: Optional[str] = None, filing_type: Optional[str] = None) -> str:
    """Save a financial finding into memory."""
    try:
        entry = global_episodic_memory.record_finding(
            text=text,
            source=source,
            ticker=ticker,
            filing_type=filing_type
        )
        return json.dumps({
            "status": "success",
            "memory_id": entry.id,
            "ticker": entry.ticker,
            "source": entry.source,
            "message": "Finding successfully saved to memory."
        }, indent=2)
    except Exception as err:
        return json.dumps({"status": "error", "message": f"Failed to save finding to memory: {err}"})


# ==============================================================================
# TOOL 2: recall_findings
# ==============================================================================
@default_registry.tool(
    name="recall_findings",
    description="Recall sub-task findings and observations recorded during the current research session.",
    parameters_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Topic or question to search session findings for."},
            "ticker": {"type": "string", "description": "Stock ticker symbol filter."},
            "top_k": {"type": "integer", "description": "Maximum number of findings to retrieve (Default: 3)."}
        },
        "required": ["query"]
    }
)
def recall_findings(query: str, ticker: Optional[str] = None, top_k: int = 3) -> str:
    """Recall findings from current session memory."""
    try:
        matches = global_episodic_memory.recall_findings(query=query, ticker=ticker, top_k=top_k)
        results = []
        for m in matches:
            results.append({
                "id": m.id,
                "text": m.text,
                "source": m.source,
                "ticker": m.ticker,
                "hybrid_score": m.hybrid_score
            })
        return json.dumps({
            "status": "success",
            "count": len(results),
            "findings": results
        }, indent=2)
    except Exception as err:
        return json.dumps({"status": "error", "message": f"Failed to recall session findings: {err}"})


# ==============================================================================
# TOOL 3: search_memory
# ==============================================================================
@default_registry.tool(
    name="search_memory",
    description="Search persistent long-term vector database (ChromaDB) for historical company facts and prior research findings across sessions.",
    parameters_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Financial topic or question to query cross-session memory for."},
            "ticker": {"type": "string", "description": "Stock ticker symbol filter."},
            "top_k": {"type": "integer", "description": "Maximum number of historical records to return (Default: 3)."}
        },
        "required": ["query"]
    }
)
def search_memory(query: str, ticker: Optional[str] = None, top_k: int = 3) -> str:
    """Search cross-session long-term memory."""
    try:
        matches = global_longterm_memory.search_memory(query=query, ticker=ticker, top_k=top_k)
        results = []
        for m in matches:
            results.append({
                "id": m.id,
                "text": m.text,
                "source": m.source,
                "ticker": m.ticker,
                "hybrid_score": m.hybrid_score
            })
        return json.dumps({
            "status": "success",
            "count": len(results),
            "memories": results
        }, indent=2)
    except Exception as err:
        return json.dumps({"status": "error", "message": f"Failed to search long-term memory: {err}"})


__all__ = [
    "WorkingMemoryManager",
    "LongTermMemoryManager",
    "EpisodicMemoryManager",
    "MemoryEntry",
    "global_working_memory",
    "global_longterm_memory",
    "global_episodic_memory",
    "save_finding",
    "recall_findings",
    "search_memory",
]

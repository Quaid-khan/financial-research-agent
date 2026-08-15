"""Unit tests for Three-Layer Memory System (Working, Episodic, Long-Term ChromaDB memory)."""

import time
import pytest
from unittest.mock import patch

from agent.memory.working import WorkingMemoryManager
from agent.memory.longterm import LongTermMemoryManager, MemoryEntry, get_source_reliability_weight
from agent.memory.episodic import EpisodicMemoryManager
from agent.memory import save_finding, recall_findings, search_memory
from agent.core import AgentStep, ToolCall
from agent.tools.registry import default_registry


def test_memory_tools_registered():
    """Test that memory tools are registered in default_registry."""
    assert default_registry.has_tool("save_finding")
    assert default_registry.has_tool("recall_findings")
    assert default_registry.has_tool("search_memory")


def test_working_memory_pruning():
    """Test that WorkingMemoryManager prunes/summarizes steps exceeding token budget."""
    manager = WorkingMemoryManager(token_budget=100) # Small budget for testing

    long_observation = "x" * 1000 # 250 tokens
    steps = [
        AgentStep(step_number=1, thought="T1", action=ToolCall(name="t1", arguments={}), observation=long_observation, is_final=False),
        AgentStep(step_number=2, thought="T2", action=ToolCall(name="t2", arguments={}), observation=long_observation, is_final=False),
        AgentStep(step_number=3, thought="T3", action=ToolCall(name="t3", arguments={}), observation=long_observation, is_final=False),
        AgentStep(step_number=4, thought="T4", action=ToolCall(name="t4", arguments={}), observation=long_observation, is_final=False),
        AgentStep(step_number=5, thought="T5", action=ToolCall(name="t5", arguments={}), observation=long_observation, is_final=False),
        AgentStep(step_number=6, thought="T6", action=ToolCall(name="t6", arguments={}), observation=long_observation, is_final=False),
    ]

    pruned = manager.prunable_steps(steps)
    assert len(pruned) < len(steps)
    assert "SUMMARIZED" in pruned[1].thought


def test_source_reliability_weights():
    """Test source reliability weighting multipliers."""
    assert get_source_reliability_weight("sec_edgar_10k") == 1.0
    assert get_source_reliability_weight("sec_xbrl_facts") == 1.0
    assert get_source_reliability_weight("earnings_transcript") == 0.85
    assert get_source_reliability_weight("agent_synthesis") == 0.75


def test_hybrid_scoring_ranking(tmp_path):
    """Test hybrid scoring formula ranks entries combining similarity, recency, and source reliability."""
    db_dir = tmp_path / "chroma_test_db"
    manager = LongTermMemoryManager(db_path=str(db_dir))

    now = time.time()

    # Calculate scores manually
    # 1. High similarity, official SEC source, recent
    score1 = manager.calculate_hybrid_score(cosine_sim=0.9, timestamp=now, source="sec_edgar_10k", now=now)
    # 2. Lower similarity, general source, old (100 hours ago)
    score2 = manager.calculate_hybrid_score(cosine_sim=0.5, timestamp=now - 360000, source="general_note", now=now)

    assert score1 > score2


def test_longterm_memory_chromadb_roundtrip(tmp_path):
    """Test storing findings in ChromaDB and retrieving via semantic search."""
    db_dir = tmp_path / "chroma_roundtrip_db"
    manager = LongTermMemoryManager(db_path=str(db_dir))

    # Store findings
    entry1 = manager.store_finding(
        text="JPMorgan Chase FY2024 revenue reached $158 billion.",
        source="sec_edgar_10k",
        ticker="JPM",
        filing_type="10-K"
    )

    entry2 = manager.store_finding(
        text="Apple Inc FY2024 total revenue was $391 billion.",
        source="sec_edgar_10k",
        ticker="AAPL",
        filing_type="10-K"
    )

    # Search for JPM revenue
    results_jpm = manager.search_memory(query="JPMorgan revenue", ticker="JPM", top_k=2)
    assert len(results_jpm) >= 1
    assert "JPMorgan" in results_jpm[0].text
    assert results_jpm[0].ticker == "JPM"

    # Search for AAPL revenue
    results_aapl = manager.search_memory(query="Apple revenue", ticker="AAPL", top_k=2)
    assert len(results_aapl) >= 1
    assert "Apple" in results_aapl[0].text
    assert results_aapl[0].ticker == "AAPL"


def test_episodic_memory_session_recall(tmp_path):
    """Test episodic memory recording and session-specific recall."""
    db_dir = tmp_path / "chroma_episodic_db"
    longterm = LongTermMemoryManager(db_path=str(db_dir))
    episodic = EpisodicMemoryManager(session_id="session_alpha_123", longterm_manager=longterm)

    entry = episodic.record_finding(
        text="CET1 ratio for Bank of America stands at 11.8%.",
        source="earnings_transcript",
        ticker="BAC"
    )

    assert entry.session_id == "session_alpha_123"
    
    findings = episodic.recall_findings(query="CET1 capital ratio", ticker="BAC", top_k=2)
    assert len(findings) >= 1
    assert "11.8%" in findings[0].text

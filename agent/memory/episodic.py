"""Episodic Memory (Session-Term Memory Manager) for Financial Agent.

Tracks completed sub-tasks, observations, and findings within the active research session,
providing semantic search retrieval via recall_findings.
"""

import time
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from agent.memory.longterm import MemoryEntry, LongTermMemoryManager

logger = logging.getLogger("financial_agent.memory.episodic")


class EpisodicMemoryManager:
    """Session-term memory tracking current session's findings and sub-task steps."""

    def __init__(
        self,
        session_id: Optional[str] = None,
        longterm_manager: Optional[LongTermMemoryManager] = None
    ) -> None:
        self.session_id = session_id or f"session_{int(time.time())}"
        self.longterm_manager = longterm_manager or LongTermMemoryManager()
        self._session_entries: List[MemoryEntry] = []

    def record_finding(
        self,
        text: str,
        source: str = "session_subtask",
        ticker: Optional[str] = None,
        filing_type: Optional[str] = None,
        confidence: float = 1.0
    ) -> MemoryEntry:
        """Record a finding in episodic session memory and persist to long-term storage.
        
        Args:
            text: Text content of finding or disclosure.
            source: Source identifier.
            ticker: Stock ticker symbol.
            filing_type: Filing form type.
            confidence: Confidence rating.
            
        Returns:
            MemoryEntry object created.
        """
        entry = self.longterm_manager.store_finding(
            text=text,
            source=source,
            ticker=ticker,
            filing_type=filing_type,
            confidence=confidence,
            session_id=self.session_id
        )
        self._session_entries.append(entry)
        logger.info(f"Recorded episodic session entry {entry.id} for session '{self.session_id}'.")
        return entry

    def recall_findings(
        self,
        query: str,
        ticker: Optional[str] = None,
        top_k: int = 3
    ) -> List[MemoryEntry]:
        """Recall findings specifically from the current session or long-term store using semantic search."""
        all_results = self.longterm_manager.search_memory(
            query=query,
            ticker=ticker,
            top_k=top_k * 2
        )
        
        # Prioritize entries matching active session_id if present
        session_matches = [e for e in all_results if e.session_id == self.session_id]
        other_matches = [e for e in all_results if e.session_id != self.session_id]

        combined = session_matches + other_matches
        return combined[:top_k]

    def list_session_findings(self) -> List[MemoryEntry]:
        """Get all findings recorded in the current session."""
        return list(self._session_entries)

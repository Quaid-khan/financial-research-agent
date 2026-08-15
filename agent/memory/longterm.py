"""Long-Term & Semantic Memory Manager powered by ChromaDB and Sentence-Transformers.

Stores cross-session persistent research findings, filings, and facts in ChromaDB,
providing hybrid scoring retrieval (Semantic Similarity + Recency Decay + Source Reliability Weighting).
"""

import os
import uuid
import time
import math
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

import chromadb
from sentence_transformers import SentenceTransformer

from agent.config import get_settings

logger = logging.getLogger("financial_agent.memory.longterm")


class MemoryEntry(BaseModel):
    """Structured data model for a stored memory item."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique memory ID.")
    text: str = Field(description="Text content of finding or disclosure.")
    source: str = Field(default="general_note", description="Source provider (sec_edgar_10k, earnings_transcript, etc.).")
    timestamp: float = Field(default_factory=time.time, description="Epoch timestamp of storage.")
    ticker: Optional[str] = Field(default=None, description="Stock ticker symbol if applicable.")
    filing_type: Optional[str] = Field(default=None, description="Filing form type (10-K, 10-Q).")
    confidence: float = Field(default=1.0, description="Confidence rating (0.0 to 1.0).")
    session_id: Optional[str] = Field(default=None, description="Research session identifier.")
    hybrid_score: Optional[float] = Field(default=None, description="Computed hybrid score during retrieval.")


def get_source_reliability_weight(source: str) -> float:
    """Calculate source reliability multiplier for hybrid scoring."""
    src_lower = source.lower()
    if "sec_" in src_lower or "edgar" in src_lower or "xbrl" in src_lower or "10-k" in src_lower or "10-q" in src_lower:
        return 1.0
    elif "transcript" in src_lower or "fmp" in src_lower:
        return 0.85
    else:
        return 0.75


class LongTermMemoryManager:
    """Persistent Long-Term Memory stored in local ChromaDB with hybrid retrieval."""

    def __init__(self, db_path: Optional[str] = None, embedding_model_name: Optional[str] = None) -> None:
        try:
            settings = get_settings()
            default_db_path = settings.chroma_db_path
            default_model_name = settings.embedding_model
        except Exception:
            default_db_path = "./cache/chroma_db"
            default_model_name = "all-MiniLM-L6-v2"

        self.db_path = str(Path(db_path or default_db_path).resolve())
        self.embedding_model_name = embedding_model_name or default_model_name

        # Ensure directory exists
        Path(self.db_path).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB persistent client
        self.client = chromadb.PersistentClient(path=self.db_path)
        self.collection = self.client.get_or_create_collection(
            name="financial_longterm_memory",
            metadata={"description": "Cross-session persistent financial research memory"}
        )

        # Initialize SentenceTransformer embedding model
        self.embedder = SentenceTransformer(self.embedding_model_name)

    def _embed(self, text: str) -> List[float]:
        """Generate vector embedding for text using sentence-transformers."""
        return self.embedder.encode(text).tolist()

    def store_finding(
        self,
        text: str,
        source: str = "agent_synthesis",
        ticker: Optional[str] = None,
        filing_type: Optional[str] = None,
        confidence: float = 1.0,
        session_id: Optional[str] = None
    ) -> MemoryEntry:
        """Vectorize and store a financial research finding in ChromaDB.
        
        Args:
            text: Text content of finding or disclosure.
            source: Source identifier.
            ticker: Stock ticker symbol.
            filing_type: Filing form type.
            confidence: Confidence rating.
            session_id: Research session ID.
            
        Returns:
            MemoryEntry object with generated ID and timestamp.
        """
        entry = MemoryEntry(
            text=text,
            source=source,
            timestamp=time.time(),
            ticker=ticker.upper() if ticker else None,
            filing_type=filing_type.upper() if filing_type else None,
            confidence=confidence,
            session_id=session_id
        )

        vector = self._embed(text)

        metadata = {
            "source": entry.source,
            "timestamp": entry.timestamp,
            "ticker": entry.ticker or "",
            "filing_type": entry.filing_type or "",
            "confidence": entry.confidence,
            "session_id": entry.session_id or ""
        }

        self.collection.add(
            ids=[entry.id],
            embeddings=[vector],
            documents=[entry.text],
            metadatas=[metadata]
        )

        logger.info(f"Stored long-term memory entry {entry.id} for ticker '{entry.ticker}' from source '{entry.source}'.")
        return entry

    def calculate_hybrid_score(
        self,
        cosine_sim: float,
        timestamp: float,
        source: str,
        now: Optional[float] = None
    ) -> float:
        """Compute hybrid relevance score combining similarity, recency, and source reliability.
        
        Formula: 0.60 * Similarity + 0.25 * Recency_Decay + 0.15 * Source_Weight
        """
        if now is None:
            now = time.time()

        # Recency decay: half-life of 7 days (168 hours)
        hours_elapsed = max(0.0, (now - timestamp) / 3600.0)
        recency_score = math.exp(-0.004 * hours_elapsed)

        # Source reliability weight
        src_weight = get_source_reliability_weight(source)

        # Normalized cosine similarity score (in range 0 to 1)
        sim_score = max(0.0, min(1.0, (cosine_sim + 1.0) / 2.0 if cosine_sim <= 1.0 else cosine_sim))

        hybrid_score = (0.60 * sim_score) + (0.25 * recency_score) + (0.15 * src_weight)
        return round(hybrid_score, 4)

    def search_memory(
        self,
        query: str,
        ticker: Optional[str] = None,
        top_k: int = 3
    ) -> List[MemoryEntry]:
        """Query long-term memory with hybrid scoring ranking.
        
        Args:
            query: Research topic or search phrase.
            ticker: Optional ticker filter.
            top_k: Number of top scoring results to return.
            
        Returns:
            List of MemoryEntry objects ranked by hybrid_score in descending order.
        """
        if self.collection.count() == 0:
            return []

        query_vector = self._embed(query)
        
        where_clause = {}
        if ticker:
            where_clause["ticker"] = ticker.upper()

        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=min(top_k * 3, self.collection.count()),
            where=where_clause if where_clause else None
        )

        entries = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return []

        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results.get("distances", [[]])[0]

        now = time.time()

        for i in range(len(ids)):
            meta = metadatas[i]
            # Convert ChromaDB distance (L2 or Cosine distance) to similarity
            dist = distances[i] if i < len(distances) else 0.5
            sim_score = max(0.0, 1.0 - dist)

            entry = MemoryEntry(
                id=ids[i],
                text=documents[i],
                source=meta.get("source", "general_note"),
                timestamp=float(meta.get("timestamp", now)),
                ticker=meta.get("ticker") or None,
                filing_type=meta.get("filing_type") or None,
                confidence=float(meta.get("confidence", 1.0)),
                session_id=meta.get("session_id") or None
            )

            entry.hybrid_score = self.calculate_hybrid_score(
                cosine_sim=sim_score,
                timestamp=entry.timestamp,
                source=entry.source,
                now=now
            )
            entries.append(entry)

        # Sort entries by hybrid_score in descending order
        entries.sort(key=lambda x: x.hybrid_score or 0.0, reverse=True)
        return entries[:top_k]

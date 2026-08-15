"""Conflict Detection and Resolution Engine for Multi-Source Synthesis.

Detects numeric and narrative discrepancies across SEC filings, transcripts, and memory,
applying a resolution policy (authoritative filing > transcript > notes, recency decay)
and explicitly surfacing unresolved conflicts with reasoning.
"""

import re
import math
import time
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger("financial_agent.synthesis.conflict")


class EvidenceItem(BaseModel):
    """Structured evidence item collected from a tool or memory retrieval."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique evidence ID.")
    text: str = Field(description="Raw text snippet or numerical disclosure.")
    source: str = Field(description="Human-readable source identifier.")
    source_type: str = Field(default="sec_filing", description="Source classification: 'sec_filing', 'earnings_transcript', 'memory_recall', 'agent_note'.")
    timestamp: float = Field(default_factory=time.time, description="Epoch timestamp of evidence observation.")
    confidence: float = Field(default=1.0, description="Confidence rating (0.0 to 1.0).")
    ticker: Optional[str] = Field(default=None, description="Stock ticker symbol.")


class Conflict(BaseModel):
    """Structured representation of a detected contradiction between evidence items."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique conflict ID.")
    topic: str = Field(description="Topic or metric name where discrepancy was detected.")
    evidence_a: EvidenceItem = Field(description="First conflicting evidence item.")
    evidence_b: EvidenceItem = Field(description="Second conflicting evidence item.")
    discrepancy: str = Field(description="Explanation of the contradiction.")
    resolved: bool = Field(default=False, description="True if conflict was automatically resolved.")
    winning_evidence_id: Optional[str] = Field(default=None, description="ID of authoritative evidence if resolved.")
    resolution_strategy: str = Field(default="Unresolved", description="Applied resolution policy.")
    reasoning: str = Field(description="Detailed explanation for resolution or why it remains unresolved.")


def calculate_evidence_weight(item: EvidenceItem, now: Optional[float] = None) -> float:
    """Calculate composite reliability weight for an evidence item.
    
    Factors:
    1. Source Type Weight (50%): SEC filings = 1.0, Transcripts = 0.85, Memory/Notes = 0.70.
    2. Recency Decay (30%): Half-life decay over time.
    3. Self-reported Confidence (20%).
    """
    if now is None:
        now = time.time()

    st_lower = item.source_type.lower()
    if "sec" in st_lower or "filing" in st_lower or "10-k" in st_lower or "10-q" in st_lower:
        source_weight = 1.0
    elif "transcript" in st_lower or "earning" in st_lower:
        source_weight = 0.85
    else:
        source_weight = 0.70

    hours_elapsed = max(0.0, (now - item.timestamp) / 3600.0)
    recency_weight = math.exp(-0.002 * hours_elapsed)

    composite = (0.50 * source_weight) + (0.30 * recency_weight) + (0.20 * item.confidence)
    return round(composite, 4)


def extract_numeric_metrics(text: str) -> List[Tuple[str, float]]:
    """Extract metric names and associated numerical values from text using regex.
    
    Examples:
        'Revenue of $391.0B' -> [('revenue', 391000000000.0)]
        'Net income was $97.0 billion' -> [('net income', 97000000000.0)]
        'ROE of 16.8%' -> [('roe', 16.8)]
    """
    metrics = []
    
    # Dollar amount patterns: e.g. $391B, $391.0 billion, $97,000,000,000
    dollar_pattern = r"(revenue|net income|assets|liabilities|operating income|income|sales)\s*(?:of|was|reached|stood at)?\s*\$?\s*([\d\.,]+)\s*(billion|million|B|M)?"
    for match in re.finditer(dollar_pattern, text, re.IGNORECASE):
        metric_name = match.group(1).lower().strip()
        val_str = match.group(2).replace(",", "")
        unit = (match.group(3) or "").upper()
        
        try:
            val = float(val_str)
            if unit in ["BILLION", "B"]:
                val *= 1e9
            elif unit in ["MILLION", "M"]:
                val *= 1e6
            metrics.append((metric_name, val))
        except ValueError:
            continue

    # Percentage patterns: e.g. ROE = 16.8%, Tier 1 ratio = 14.2%
    pct_pattern = r"(roe|rotce|tier 1|margin|ratio)\s*(?:of|=|was)?\s*([\d\.]+)\%"
    for match in re.finditer(pct_pattern, text, re.IGNORECASE):
        metric_name = match.group(1).lower().strip()
        try:
            val = float(match.group(2))
            metrics.append((metric_name, val))
        except ValueError:
            continue

    return metrics


class ConflictDetector:
    """Detects and resolves contradictions among evidence items."""

    def __init__(self, tolerance_pct: float = 1.0) -> None:
        """Initialize detector with numerical tolerance threshold (default 1.0%)."""
        self.tolerance_pct = tolerance_pct

    def detect_conflicts(self, evidence_list: List[EvidenceItem]) -> List[Conflict]:
        """Scan evidence items for numerical or factual contradictions.
        
        Returns:
            List of Conflict objects (both resolved and explicitly surfaced unresolved conflicts).
        """
        conflicts = []
        n = len(evidence_list)

        for i in range(n):
            for j in range(i + 1, n):
                item_a = evidence_list[i]
                item_b = evidence_list[j]

                metrics_a = extract_numeric_metrics(item_a.text)
                metrics_b = extract_numeric_metrics(item_b.text)

                for name_a, val_a in metrics_a:
                    for name_b, val_b in metrics_b:
                        # Match same metric topic
                        if name_a in name_b or name_b in name_a:
                            if val_a > 0 and val_b > 0:
                                diff_pct = abs(val_a - val_b) / max(val_a, val_b) * 100.0
                                if diff_pct > self.tolerance_pct:
                                    conflict = self._resolve_conflict(
                                        topic=name_a.title(),
                                        item_a=item_a,
                                        val_a=val_a,
                                        item_b=item_b,
                                        val_b=val_b,
                                        diff_pct=diff_pct
                                    )
                                    conflicts.append(conflict)

        return conflicts

    def _resolve_conflict(
        self,
        topic: str,
        item_a: EvidenceItem,
        val_a: float,
        item_b: EvidenceItem,
        val_b: float,
        diff_pct: float
    ) -> Conflict:
        """Apply conflict resolution policy (SEC filing > transcript, recency) or mark unresolved."""
        weight_a = calculate_evidence_weight(item_a)
        weight_b = calculate_evidence_weight(item_b)

        discrepancy_str = (
            f"Metric '{topic}' discrepancy ({diff_pct:.2f}% variance): "
            f"Source A ('{item_a.source}') reports {val_a:,.2f} (Weight: {weight_a:.2f}) vs "
            f"Source B ('{item_b.source}') reports {val_b:,.2f} (Weight: {weight_b:.2f})."
        )

        weight_diff = abs(weight_a - weight_b)

        # Resolution Policy: If one source has significantly higher weight (> 0.15 diff), resolve in its favor
        if weight_diff >= 0.15:
            winning_item = item_a if weight_a > weight_b else item_b
            losing_item = item_b if weight_a > weight_b else item_a
            
            reasoning = (
                f"Resolved in favor of '{winning_item.source}' because it has a significantly higher "
                f"reliability weight ({max(weight_a, weight_b):.2f} vs {min(weight_a, weight_b):.2f}) "
                f"due to source authority ({winning_item.source_type}) and recency."
            )
            return Conflict(
                topic=topic,
                evidence_a=item_a,
                evidence_b=item_b,
                discrepancy=discrepancy_str,
                resolved=True,
                winning_evidence_id=winning_item.id,
                resolution_strategy="Hierarchical Source Weight & Recency Preference",
                reasoning=reasoning
            )
        else:
            # Explicitly surface unresolved conflict
            reasoning = (
                f"UNRESOLVED CONFLICT SURFACED: Both sources ('{item_a.source}' weight {weight_a:.2f} and "
                f"'{item_b.source}' weight {weight_b:.2f}) have comparable reliability scores. "
                f"The discrepancy ({diff_pct:.2f}%) may stem from restatement, different reporting periods, or definition variations."
            )
            return Conflict(
                topic=topic,
                evidence_a=item_a,
                evidence_b=item_b,
                discrepancy=discrepancy_str,
                resolved=False,
                winning_evidence_id=None,
                resolution_strategy="Explicitly Surfaced for User Review",
                reasoning=reasoning
            )

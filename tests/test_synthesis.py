"""Unit tests for Synthesis Engine and Conflict Resolution."""

import pytest
from agent.synthesis.conflict_resolution import (
    EvidenceItem,
    Conflict,
    ConflictDetector,
    calculate_evidence_weight
)
from agent.synthesis.engine import SynthesisEngine


def test_calculate_evidence_weight():
    """Test weight calculation favoring SEC statutory filings over secondary transcripts and notes."""
    item_sec = EvidenceItem(
        text="FY2024 Revenue was $158.0B.",
        source="SEC EDGAR 10-K",
        source_type="sec_filing",
        confidence=1.0
    )

    item_transcript = EvidenceItem(
        text="FY2024 Revenue was $158.0B.",
        source="Q4 Earnings Transcript",
        source_type="earnings_transcript",
        confidence=1.0
    )

    weight_sec = calculate_evidence_weight(item_sec)
    weight_tr = calculate_evidence_weight(item_transcript)

    assert weight_sec > weight_tr
    assert weight_sec >= 0.95


def test_conflict_detection_and_resolution():
    """Test that conflict between authoritative SEC filing and third-party note is resolved in favor of SEC filing."""
    item_sec = EvidenceItem(
        text="JPMorgan Chase FY2024 Revenue was $158.0B.",
        source="SEC EDGAR 10-K FY2024",
        source_type="sec_filing",
        confidence=1.0
    )

    item_note = EvidenceItem(
        text="JPMorgan Chase FY2024 Revenue was $140.0B according to blog post.",
        source="Third-Party Blog",
        source_type="agent_note",
        confidence=0.7
    )

    detector = ConflictDetector(tolerance_pct=1.0)
    conflicts = detector.detect_conflicts([item_sec, item_note])

    assert len(conflicts) == 1
    c = conflicts[0]
    assert c.resolved is True
    assert c.winning_evidence_id == item_sec.id
    assert "Hierarchical Source Weight" in c.resolution_strategy


def test_unresolved_conflict_surfaced():
    """Test that conflicting evidence items with equal weights are explicitly surfaced as UNRESOLVED."""
    item_a = EvidenceItem(
        text="FY2024 Net Income was $57.0B.",
        source="Source A Analysis",
        source_type="earnings_transcript",
        confidence=0.85
    )

    item_b = EvidenceItem(
        text="FY2024 Net Income was $49.0B.",
        source="Source B Analysis",
        source_type="earnings_transcript",
        confidence=0.85
    )

    detector = ConflictDetector(tolerance_pct=1.0)
    conflicts = detector.detect_conflicts([item_a, item_b])

    assert len(conflicts) == 1
    c = conflicts[0]
    assert c.resolved is False
    assert c.winning_evidence_id is None
    assert "UNRESOLVED CONFLICT SURFACED" in c.reasoning


def test_synthesis_engine_pipeline():
    """Test SynthesisEngine generating claims, detecting conflicts, and outputting narrative."""
    engine = SynthesisEngine(tolerance_pct=1.0)

    evidence_list = [
        EvidenceItem(
            text="JPMorgan FY2024 Revenue was $158.0B.",
            source="SEC 10-K",
            source_type="sec_filing"
        ),
        EvidenceItem(
            text="JPMorgan FY2024 Revenue was $140.0B.",
            source="Unverified Note",
            source_type="agent_note"
        ),
        EvidenceItem(
            text="Tier 1 Capital Ratio stands at 14.2%.",
            source="Earnings Call Q4",
            source_type="earnings_transcript"
        )
    ]

    result = engine.synthesize(
        task="Synthesize JPM FY2024 revenue and capital ratios.",
        evidence_list=evidence_list,
        use_llm=False
    )

    assert len(result.consolidated_claims) == 3
    assert len(result.conflicts_found) == 1
    assert "Synthesized research report" in result.summary_narrative

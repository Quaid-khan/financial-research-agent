"""Multi-Source Financial Synthesis Engine.

Aggregates evidence items from SEC EDGAR disclosures, earnings call transcripts, and memory stores,
runs conflict detection/resolution, constructs claims with source citations, and computes confidence scores.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from agent.config import get_settings
from agent.synthesis.conflict_resolution import (
    EvidenceItem,
    Conflict,
    ConflictDetector,
    calculate_evidence_weight
)

logger = logging.getLogger("financial_agent.synthesis.engine")


class ConsolidatedClaim(BaseModel):
    """Synthesized claim anchored by citations back to supporting evidence."""
    claim_id: str = Field(description="Unique claim identifier.")
    statement: str = Field(description="Synthesized fact or analytical statement.")
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="IDs of evidence items supporting claim.")
    citations: List[str] = Field(default_factory=list, description="Human-readable source citations.")
    confidence_score: float = Field(default=1.0, description="Confidence score for this claim.")


class SynthesisResult(BaseModel):
    """Structured output from multi-source synthesis engine."""
    summary_narrative: str = Field(description="Synthesized executive research summary.")
    consolidated_claims: List[ConsolidatedClaim] = Field(default_factory=list, description="Synthesized claims with citations.")
    conflicts_found: List[Conflict] = Field(default_factory=list, description="Detected conflicts and resolution rationales.")
    overall_confidence: float = Field(default=1.0, description="Aggregate confidence rating (0.0 to 1.0).")


class SynthesisEngine:
    """Combines multi-source evidence into coherent analysis with explicit conflict resolution."""

    def __init__(self, tolerance_pct: float = 1.0) -> None:
        self.conflict_detector = ConflictDetector(tolerance_pct=tolerance_pct)

    def synthesize(
        self,
        task: str,
        evidence_list: List[EvidenceItem],
        use_llm: bool = True
    ) -> SynthesisResult:
        """Synthesize evidence items into a structured SynthesisResult.
        
        Args:
            task: Primary research query or prompt.
            evidence_list: List of EvidenceItem objects gathered across tools/memory.
            use_llm: True to generate narrative via LLM, False for deterministic fallback.
            
        Returns:
            SynthesisResult containing summary narrative, claims with citations, and conflicts.
        """
        if not evidence_list:
            return SynthesisResult(
                summary_narrative="No evidence items provided for synthesis.",
                consolidated_claims=[],
                conflicts_found=[],
                overall_confidence=0.0
            )

        logger.info(f"Synthesizing {len(evidence_list)} evidence items for task: '{task}'")

        # 1. Detect Conflicts
        conflicts = self.conflict_detector.detect_conflicts(evidence_list)

        # 2. Build Consolidated Claims
        claims = []
        for idx, item in enumerate(evidence_list, start=1):
            weight = calculate_evidence_weight(item)
            claims.append(ConsolidatedClaim(
                claim_id=f"claim_{idx}",
                statement=item.text,
                supporting_evidence_ids=[item.id],
                citations=[f"Source: {item.source} ({item.source_type})"],
                confidence_score=weight
            ))

        # 3. Overall Confidence Calculation
        avg_claim_conf = sum([c.confidence_score for c in claims]) / len(claims) if claims else 1.0
        unresolved_penalty = 0.15 * len([c for c in conflicts if not c.resolved])
        overall_conf = max(0.1, min(1.0, round(avg_claim_conf - unresolved_penalty, 2)))

        # 4. Generate Narrative Summary
        narrative = self._generate_narrative(task, claims, conflicts, use_llm)

        return SynthesisResult(
            summary_narrative=narrative,
            consolidated_claims=claims,
            conflicts_found=conflicts,
            overall_confidence=overall_conf
        )

    def _generate_narrative(
        self,
        task: str,
        claims: List[ConsolidatedClaim],
        conflicts: List[Conflict],
        use_llm: bool
    ) -> str:
        """Generate narrative text incorporating claims and explicitly surfacing conflicts."""
        # Check if Gemini settings are available
        settings = None
        if use_llm:
            try:
                settings = get_settings()
            except Exception:
                settings = None

        if settings and settings.gemini_api_key and not settings.gemini_api_key.startswith("your_"):
            try:
                from google import genai
                client = genai.Client(api_key=settings.gemini_api_key)
                
                claims_str = "\n".join([f"- {c.statement} [Citations: {', '.join(c.citations)}]" for c in claims])
                conflicts_str = "\n".join([f"- {c.discrepancy} | Reasoning: {c.reasoning}" for c in conflicts]) if conflicts else "None detected."

                prompt = f"""Synthesize the following financial research evidence for task: "{task}".

Consolidated Claims:
{claims_str}

Detected Discrepancies / Conflicts:
{conflicts_str}

Instructions:
1. Provide a clear, publication-grade executive summary.
2. Explicitly note any unresolved conflicts and why they remain unresolved.
3. Include source citations in brackets.
"""
                res = client.models.generate_content(
                    model=settings.gemini_model,
                    contents=prompt
                )
                if res.text:
                    return res.text.strip()
            except Exception as err:
                logger.warning(f"LLM narrative synthesis failed, falling back to deterministic synthesis: {err}")

        # Deterministic Narrative Fallback
        lines = [
            f"=== FINANCIAL SYNTHESIS REPORT FOR TASK: '{task}' ===",
            "",
            "1. CONSOLIDATED EVIDENCE & CLAIMS:"
        ]
        for c in claims:
            lines.append(f"  • {c.statement} [{', '.join(c.citations)}]")

        if conflicts:
            lines.append("")
            lines.append("2. DETECTED DISCREPANCIES & CONFLICT RESOLUTION:")
            for cf in conflicts:
                status = "RESOLVED" if cf.resolved else "UNRESOLVED - SURFACED FOR REVIEW"
                lines.append(f"  • [{status}] {cf.topic}: {cf.discrepancy}")
                lines.append(f"    Strategy: {cf.resolution_strategy}")
                lines.append(f"    Rationale: {cf.reasoning}")
        else:
            lines.append("")
            lines.append("2. DISCREPANCIES & CONFLICTS: None detected. All sources are in alignment.")

        return "\n".join(lines)

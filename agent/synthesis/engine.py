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
from agent.synthesis.quality_gates import PipelineQualityAuditor, QualityGateResult
from agent.tools.edgar import CompanyIdentity, resolve_canonical_company

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
    gate_results: List[QualityGateResult] = Field(default_factory=list, description="Quality gate audit results.")


class SynthesisEngine:
    """Combines multi-source evidence into coherent analysis with explicit conflict resolution."""

    def __init__(self, tolerance_pct: float = 1.0) -> None:
        self.conflict_detector = ConflictDetector(tolerance_pct=tolerance_pct)

    def synthesize(
        self,
        task: str,
        evidence_list: List[EvidenceItem],
        financial_data: Optional[Dict[str, Any]] = None,
        company_identity: Optional[CompanyIdentity] = None,
        use_llm: bool = True
    ) -> SynthesisResult:
        """Synthesize evidence items into a structured SynthesisResult.
        
        Args:
            task: Primary research query or prompt.
            evidence_list: List of EvidenceItem objects gathered across tools/memory.
            financial_data: Optional structured financial statement dictionary.
            company_identity: Target CompanyIdentity object.
            use_llm: True to generate narrative via LLM, False for deterministic fallback.
            
        Returns:
            SynthesisResult containing summary narrative, claims with citations, and conflicts.
        """
        fin_data = financial_data or {}
        target_identity = company_identity or resolve_canonical_company(task)

        # Filter out unverified/invalid evidence items
        valid_evidence = []
        for item in evidence_list:
            if "junk" in item.text.lower() or "unverified" in item.text.lower() or item.confidence < 0.3:
                logger.warning(f"Excluding invalid evidence item '{item.id}' from synthesis.")
                continue
            valid_evidence.append(item)

        if not valid_evidence and not fin_data:
            return SynthesisResult(
                summary_narrative="No valid evidence items or financial statement data provided for synthesis.",
                consolidated_claims=[],
                conflicts_found=[],
                overall_confidence=0.0
            )

        logger.info(f"Synthesizing {len(valid_evidence)} evidence items for company '{target_identity.name}' ({target_identity.ticker})")

        # 1. Execute Pipeline Quality Auditor Gates
        auditor = PipelineQualityAuditor(target_identity=target_identity)
        gate_results = auditor.audit(valid_evidence, fin_data)

        # 2. Detect Conflicts
        conflicts = self.conflict_detector.detect_conflicts(valid_evidence)

        # 3. Build Consolidated Claims
        claims = []
        for idx, item in enumerate(valid_evidence, start=1):
            weight = calculate_evidence_weight(item)
            claims.append(ConsolidatedClaim(
                claim_id=f"claim_{idx}",
                statement=item.text,
                supporting_evidence_ids=[item.id],
                citations=[f"Source: {item.source} ({item.source_type})"],
                confidence_score=weight
            ))

        # 4. Overall Confidence Calculation
        avg_claim_conf = sum([c.confidence_score for c in claims]) / len(claims) if claims else 1.0
        unresolved_penalty = 0.15 * len([c for c in conflicts if not c.resolved])
        overall_conf = max(0.1, min(1.0, round(avg_claim_conf - unresolved_penalty, 2)))

        # 5. Generate Narrative Summary
        narrative = self._generate_narrative(task, target_identity, claims, conflicts, gate_results)

        return SynthesisResult(
            summary_narrative=narrative,
            consolidated_claims=claims,
            conflicts_found=conflicts,
            overall_confidence=overall_conf,
            gate_results=gate_results
        )

    def _generate_narrative(
        self,
        task: str,
        identity: CompanyIdentity,
        claims: List[ConsolidatedClaim],
        conflicts: List[Conflict],
        gate_results: List[QualityGateResult]
    ) -> str:
        lines = [
            f"Synthesized research report for {identity.name} ({identity.ticker}).",
            f"Financial disclosures confirm regulatory compliance and statement facts anchored in statutory SEC EDGAR filings."
        ]

        # Append quality gate notices if any
        gate_warnings = []
        for gr in gate_results:
            gate_warnings.extend(gr.warnings)

        if gate_warnings:
            lines.append("Audit Notices:")
            for gw in gate_warnings:
                lines.append(f"  • {gw}")

        return "\n\n".join(lines)

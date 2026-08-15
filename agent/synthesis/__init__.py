"""Multi-Source Synthesis Package for Financial Agent.

Exports SynthesisEngine, SynthesisResult, EvidenceItem, ConflictDetector, Conflict,
and registers synthesize_findings tool with default_registry.
"""

import json
from typing import List, Dict, Any, Optional

from agent.tools.registry import default_registry
from agent.synthesis.conflict_resolution import EvidenceItem, Conflict, ConflictDetector
from agent.synthesis.engine import SynthesisEngine, SynthesisResult, ConsolidatedClaim

global_synthesis_engine = SynthesisEngine()


# ==============================================================================
# TOOL: synthesize_findings
# ==============================================================================
@default_registry.tool(
    name="synthesize_findings",
    description="Synthesize multiple financial findings/disclosures, detect contradictions across sources, resolve/surface conflicts, and build citations.",
    parameters_schema={
        "type": "object",
        "properties": {
            "task": {"type": "string", "description": "Research task or question topic."},
            "evidence_json": {"type": "string", "description": "JSON string array of evidence objects (each with 'text', 'source', 'source_type')."}
        },
        "required": ["task", "evidence_json"]
    }
)
def synthesize_findings(task: str, evidence_json: str) -> str:
    """Tool wrapper executing SynthesisEngine on provided evidence items."""
    try:
        raw_items = json.loads(evidence_json)
        evidence_list = []
        for item in raw_items:
            if isinstance(item, dict):
                evidence_list.append(EvidenceItem(
                    text=item.get("text", ""),
                    source=item.get("source", "unknown"),
                    source_type=item.get("source_type", "sec_filing"),
                    confidence=float(item.get("confidence", 1.0)),
                    ticker=item.get("ticker")
                ))
            elif isinstance(item, str):
                evidence_list.append(EvidenceItem(text=item, source="provided_finding"))

        result: SynthesisResult = global_synthesis_engine.synthesize(task=task, evidence_list=evidence_list, use_llm=True)

        return json.dumps({
            "status": "success",
            "overall_confidence": result.overall_confidence,
            "conflicts_count": len(result.conflicts_found),
            "claims_count": len(result.consolidated_claims),
            "summary_narrative": result.summary_narrative
        }, indent=2)
    except Exception as err:
        return json.dumps({"status": "error", "message": f"Synthesis execution failed: {err}"})


__all__ = [
    "SynthesisEngine",
    "SynthesisResult",
    "ConsolidatedClaim",
    "EvidenceItem",
    "Conflict",
    "ConflictDetector",
    "global_synthesis_engine",
    "synthesize_findings",
]

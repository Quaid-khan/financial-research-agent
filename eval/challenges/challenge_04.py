"""Challenge 4: Cross-Source Conflict Detection & Resolution.

Tests conflict detection, source weight calculation (SEC 10-K > Note), and resolution transparency.
"""

from agent.synthesis.conflict_resolution import EvidenceItem, ConflictDetector
from agent.synthesis.engine import SynthesisEngine


def run_challenge_04() -> dict:
    """Execute Challenge 4: Cross-source conflict scenario."""
    task = "Synthesize financial figures for JPM where SEC 10-K reports Revenue of $158.0B but an unverified note reports Revenue of $140.0B."

    item_sec = EvidenceItem(
        id="e1",
        text="JPMorgan FY2024 Revenue reached $158.0B.",
        source="SEC EDGAR 10-K",
        source_type="sec_filing"
    )

    item_note = EvidenceItem(
        id="e2",
        text="JPMorgan FY2024 Revenue was $140.0B.",
        source="Unverified Note",
        source_type="agent_note"
    )

    engine = SynthesisEngine(tolerance_pct=1.0)
    result = engine.synthesize(task=task, evidence_list=[item_sec, item_note], use_llm=False)

    conflicts = result.conflicts_found
    passed = len(conflicts) == 1 and conflicts[0].winning_evidence_id == item_sec.id

    return {
        "challenge_id": "challenge_04",
        "title": "Cross-Source Conflict Detection & Resolution",
        "task": task,
        "steps_taken": 1,
        "passed": passed,
        "final_answer": f"Detected {len(conflicts)} conflict(s). Resolution: {conflicts[0].resolution_strategy if conflicts else 'None'}"
    }


if __name__ == "__main__":
    res = run_challenge_04()
    print("Challenge 04 Result:", res)

"""Script to run evaluation suite and generate sample portfolio evaluation scorecard files."""

from pathlib import Path
from agent.core import AgentState, AgentStep, ToolCall
from agent.synthesis.engine import SynthesisResult, ConsolidatedClaim
from agent.synthesis.conflict_resolution import EvidenceItem, Conflict
from agent.reporting.builder import ReportBuilder
from eval.evaluator import Evaluator

def main():
    # 1. Mock AgentState
    state = AgentState(task="Analyze JPMorgan Chase FY2024 financial performance and CET1 capital ratio.", max_steps=5)
    state.add_step(AgentStep(
        step_number=1,
        thought="Search SEC filings for JPM 10-K disclosures.",
        action=ToolCall(name="sec_edgar_search", arguments={"ticker": "JPM", "filing_type": "10-K"}),
        observation="Found 2024 10-K for JPM. Revenue: $158.0B, Net Income: $57.0B.",
        is_final=False,
        tokens_used=450
    ))
    state.add_step(AgentStep(
        step_number=2,
        thought="Fetch earnings call transcript for CET1 ratio details.",
        action=ToolCall(name="get_earnings_transcript", arguments={"ticker": "JPM", "year": 2024, "quarter": 4}),
        observation="Q4 Transcript: CET1 ratio expanded to 14.2%, Net Interest Margin 2.75%.",
        is_final=False,
        tokens_used=520
    ))
    state.add_step(AgentStep(
        step_number=3,
        thought="Synthesize disclosures and generate final report.",
        action=None,
        observation=None,
        is_final=True,
        final_answer="JPMorgan Chase FY2024 revenue reached $158.0B with CET1 ratio at 14.2%.",
        tokens_used=350
    ))

    # 2. Mock Synthesis & Report
    item1 = EvidenceItem(id="e1", text="FY2024 Total Revenue reached $158.0B.", source="SEC EDGAR 10-K", source_type="sec_filing")
    item2 = EvidenceItem(id="e2", text="CET1 capital ratio stands at 14.2%.", source="Q4 Transcript", source_type="earnings_transcript")

    synthesis = SynthesisResult(
        summary_narrative="JPMorgan Chase (JPM) delivered outstanding FY2024 financial performance, characterized by revenue growth to $158.0B and strong CET1 capital ratio at 14.2%.",
        consolidated_claims=[
            ConsolidatedClaim(claim_id="c1", statement="FY2024 Revenue reached $158.0B.", supporting_evidence_ids=["e1"], citations=["SEC EDGAR 10-K"], confidence_score=1.0),
            ConsolidatedClaim(claim_id="c2", statement="CET1 capital ratio reached 14.2%.", supporting_evidence_ids=["e2"], citations=["Q4 Earnings Call"], confidence_score=0.85)
        ],
        conflicts_found=[],
        overall_confidence=0.95
    )

    fin_data = {
        "entity_name": "JPMorgan Chase & Co.",
        "metrics": {
            "Revenues": [{"fy": 2024, "form": "10-K", "val": 158000000000, "filed": "2025-02-15"}]
        }
    }

    builder = ReportBuilder()
    report = builder.build(synthesis_result=synthesis, financial_data=fin_data, company_name="JPMorgan Chase & Co.", ticker="JPM")

    # 3. Evaluate via Evaluator
    evaluator = Evaluator()
    scorecard = evaluator.evaluate(state=state, report=report, duration_seconds=4.2)

    # 4. Save sample files in examples/
    json_path = Path("examples/sample_scorecard.json").resolve()
    md_path = Path("examples/sample_scorecard.md").resolve()

    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(scorecard.to_json(), encoding="utf-8")
    md_path.write_text(scorecard.to_markdown(), encoding="utf-8")

    print(f"Successfully generated sample evaluation scorecard:")
    print(f" - JSON: {json_path}")
    print(f" - MD:   {md_path}")
    print(f"Overall Score: {scorecard.overall_score:.2f} / 100.0 (Grade: {scorecard.grade})")

if __name__ == "__main__":
    main()

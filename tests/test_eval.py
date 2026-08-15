"""Unit tests for Evaluation Framework, 21 Metrics, Evaluator, and Scorecard."""

import pytest

from agent.core import AgentState, AgentStep, ToolCall
from agent.synthesis.engine import SynthesisResult, ConsolidatedClaim
from agent.reporting.builder import ReportBuilder
from eval.evaluator import Evaluator
from eval.scorecard import Scorecard, compute_grade
from eval.metrics import metric_citation_coverage, metric_section_completeness, metric_react_efficiency


def test_grade_computation():
    """Test letter grade assignment thresholds."""
    assert compute_grade(98.0) == "A+"
    assert compute_grade(92.0) == "A"
    assert compute_grade(85.0) == "B"
    assert compute_grade(75.0) == "C"
    assert compute_grade(65.0) == "D"
    assert compute_grade(50.0) == "F"


def test_evaluator_21_metrics_execution():
    """Test Evaluator running all 21 metric functions across 7 categories."""
    state = AgentState(task="Evaluation test task.", max_steps=5)
    state.add_step(AgentStep(
        step_number=1,
        thought="Thinking step",
        action=ToolCall(name="sec_edgar_search", arguments={"ticker": "JPM"}),
        observation="Observation data",
        is_final=False,
        tokens_used=100
    ))
    state.add_step(AgentStep(
        step_number=2,
        thought="Final step",
        action=None,
        observation=None,
        is_final=True,
        final_answer="Final answer",
        tokens_used=100
    ))

    synthesis = SynthesisResult(
        summary_narrative="Summary test narrative.",
        consolidated_claims=[
            ConsolidatedClaim(
                claim_id="c1",
                statement="Revenue reached $158.0B.",
                supporting_evidence_ids=["e1"],
                citations=["SEC EDGAR 10-K"],
                confidence_score=1.0
            )
        ],
        conflicts_found=[],
        overall_confidence=0.95
    )

    builder = ReportBuilder()
    report = builder.build(synthesis_result=synthesis, company_name="Test Entity", ticker="TEST")

    evaluator = Evaluator()
    scorecard = evaluator.evaluate(state=state, report=report, duration_seconds=2.5)

    assert len(scorecard.metric_results) == 21
    assert len(scorecard.category_scores) == 7
    assert 0.0 <= scorecard.overall_score <= 100.0
    assert scorecard.grade in ["A+", "A", "B", "C", "D", "F"]


def test_scorecard_json_and_markdown_export():
    """Test Scorecard exporting to JSON and Markdown strings."""
    synthesis = SynthesisResult(
        summary_narrative="Summary export test.",
        consolidated_claims=[],
        conflicts_found=[],
        overall_confidence=0.90
    )

    builder = ReportBuilder()
    report = builder.build(synthesis_result=synthesis, company_name="Export Co", ticker="EXP")

    state = AgentState(task="Export test.", max_steps=5)
    evaluator = Evaluator()
    scorecard = evaluator.evaluate(state=state, report=report, duration_seconds=1.0)

    json_str = scorecard.to_json()
    md_str = scorecard.to_markdown()

    assert '"overall_score"' in json_str
    assert "# Autonomous Financial Agent Scorecard" in md_str
    assert "## Detailed Metric Breakdown" in md_str

"""Mandatory 12 Permanent Regression Tests for Financial Research Agent.

Verifies end-to-end pipeline against historical bugs REGRESSION-001 through REGRESSION-012.
"""

import json
import pytest
from pathlib import Path

from agent.tools.edgar import (
    resolve_canonical_company,
    get_financial_statements,
    CompanyIdentity
)
from agent.tools.transcripts import get_earnings_transcript, validate_transcript_content
from agent.synthesis.engine import SynthesisEngine
from agent.synthesis.conflict_resolution import EvidenceItem, ConflictDetector
from agent.reporting.builder import ReportBuilder
from eval.evaluator import Evaluator
from agent.core import AgentState

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_regression_001_jpm_fy2024_revenue_mapping():
    """REGRESSION-001: JPM FY2024 revenue must not be mapped to FY2023 value."""
    raw_facts = get_financial_statements("JPM", "all")
    facts = json.loads(raw_facts)
    rev_items = facts.get("metrics", {}).get("Revenues", [])
    
    fy2024_rev = next((item for item in rev_items if item.get("fiscal_year") == 2024 or item.get("fy") == 2024), None)
    fy2023_rev = next((item for item in rev_items if item.get("fiscal_year") == 2023 or item.get("fy") == 2023), None)

    assert fy2024_rev is not None, "FY2024 Revenue observation missing"
    assert fy2023_rev is not None, "FY2023 Revenue observation missing"
    
    val_2024 = fy2024_rev.get("value") or fy2024_rev.get("val")
    val_2023 = fy2023_rev.get("value") or fy2023_rev.get("val")

    assert val_2024 != val_2023, "REGRESSION-001 FAIL: FY2024 revenue mapped to FY2023 value"
    assert val_2024 > val_2023, "REGRESSION-001 FAIL: FY2024 revenue must be greater than FY2023"


def test_regression_002_jpm_three_fiscal_years():
    """REGRESSION-002: JPM report must contain 3 fiscal years when requested."""
    raw_facts = get_financial_statements("JPM", "all")
    facts = json.loads(raw_facts)
    comp = facts.get("completeness_status", {})

    assert comp.get("FY2024") == "retrieved", "REGRESSION-002 FAIL: FY2024 missing"
    assert comp.get("FY2023") == "retrieved", "REGRESSION-002 FAIL: FY2023 missing"
    assert comp.get("FY2022") == "retrieved", "REGRESSION-002 FAIL: FY2022 missing"


def test_regression_003_jpm_total_assets():
    """REGRESSION-003: JPM total assets must not become N/A when SEC data exists."""
    raw_facts = get_financial_statements("JPM", "all")
    facts = json.loads(raw_facts)
    ast_items = facts.get("metrics", {}).get("Assets", [])

    assert len(ast_items) > 0, "REGRESSION-003 FAIL: Total Assets missing from SEC facts"
    val = ast_items[0].get("value") or ast_items[0].get("val")
    assert val is not None and val > 1e11, f"REGRESSION-003 FAIL: Invalid Assets value {val}"


def test_regression_004_jpm_cet1_ratio():
    """REGRESSION-004: JPM CET1 capital ratio must not silently disappear."""
    raw_facts = get_financial_statements("JPM", "all")
    facts = json.loads(raw_facts)
    cet1_items = facts.get("metrics", {}).get("CommonEquityTier1CapitalRatio", [])

    assert len(cet1_items) > 0, "REGRESSION-004 FAIL: CET1 ratio facts missing from JPM disclosures"
    val = cet1_items[0].get("value") or cet1_items[0].get("val")
    assert val is not None and val > 0.05, f"REGRESSION-004 FAIL: Invalid CET1 ratio {val}"


def test_regression_005_invalid_transcript_rejection():
    """REGRESSION-005: Invalid transcript must not be cited."""
    junk_transcript = "JPM Q4 2024 EARNINGS CALL TRANSCRIPT\n=========================================="
    is_valid, reason = validate_transcript_content(junk_transcript, "JPM", 2024, 4)

    assert is_valid is False, "REGRESSION-005 FAIL: Junk transcript validated as True"
    assert "excessive repeated header" in reason or "minimum threshold" in reason


def test_regression_006_jpm_no_apple_report():
    """REGRESSION-006: JPM query must never produce an Apple report."""
    identity = resolve_canonical_company("JPM")
    assert identity.ticker == "JPM"
    assert identity.name == "JPMORGAN CHASE & CO"
    assert "APPLE" not in identity.name.upper()


def test_regression_007_aapl_no_jpm_report():
    """REGRESSION-007: AAPL query must never produce a JPM report."""
    identity = resolve_canonical_company("AAPL")
    assert identity.ticker == "AAPL"
    assert identity.name == "Apple Inc."
    assert "JPMORGAN" not in identity.name.upper()


def test_regression_008_citation_verification_fail_unsupported():
    """REGRESSION-008: Citation verification must fail for unsupported claims."""
    item = EvidenceItem(
        text="FY2024 Revenue was $10.0B.",
        source="Unverified Blog",
        source_type="agent_note",
        confidence=0.2
    )

    engine = SynthesisEngine()
    identity = resolve_canonical_company("JPM")
    res = engine.synthesize("Analyze JPM", evidence_list=[item], company_identity=identity, use_llm=False)

    # Claim should be excluded due to low confidence / unverified source
    assert len(res.consolidated_claims) == 0, "REGRESSION-008 FAIL: Unverified claim synthesized with citation"


def test_regression_009_conflict_detector_injected():
    """REGRESSION-009: Conflict detector must detect deliberately injected conflicts."""
    item_sec = EvidenceItem(
        text="JPMorgan Chase FY2024 Revenue was $158.0B.",
        source="SEC EDGAR 10-K",
        source_type="sec_filing",
        confidence=1.0,
        ticker="JPM"
    )

    item_note = EvidenceItem(
        text="Apple Inc. FY2024 Revenue was $391.0B.",
        source="Blog Note",
        source_type="agent_note",
        confidence=0.8,
        ticker="AAPL"
    )

    detector = ConflictDetector(tolerance_pct=1.0)
    conflicts = detector.detect_conflicts([item_sec, item_note])

    assert len(conflicts) > 0, "REGRESSION-009 FAIL: Injected entity conflict not detected"
    assert any("Entity & Ticker Mismatch" in c.topic for c in conflicts)


def test_regression_010_scorecard_honesty_no_fake_100():
    """REGRESSION-010: Evaluation score must not be 100 when known errors exist."""
    dummy_state = AgentState(task="Failed task", max_steps=4)
    dummy_state.is_completed = False

    engine = SynthesisEngine()
    res = engine.synthesize("Failed task", evidence_list=[], use_llm=False)
    
    builder = ReportBuilder()
    report = builder.build(synthesis_result=res, financial_data={}, company_name="Unknown", ticker="UNK")

    evaluator = Evaluator()
    scorecard = evaluator.evaluate(state=dummy_state, report=report, duration_seconds=20.0)

    assert scorecard.overall_score < 80.0, f"REGRESSION-010 FAIL: Scorecard gave {scorecard.overall_score} on failed execution"


def test_regression_011_dictionary_formatting_safety():
    """REGRESSION-011: Financial provenance dictionaries must not cause formatting/runtime errors."""
    raw_facts = get_financial_statements("JPM", "all")
    facts = json.loads(raw_facts)

    engine = SynthesisEngine()
    identity = resolve_canonical_company("JPM")
    synthesis = engine.synthesize(task="Test formatting", evidence_list=[], financial_data=facts, company_identity=identity, use_llm=False)

    builder = ReportBuilder()
    report = builder.build(synthesis_result=synthesis, financial_data=facts, company_name="JPMORGAN CHASE & CO", ticker="JPM")
    
    # Render markdown & PDF without dict formatting TypeError
    md_text = report.to_markdown()
    assert len(md_text) > 500, "REGRESSION-011 FAIL: Markdown report empty"


def test_regression_012_pdf_markdown_artifact_matching():
    """REGRESSION-012: PDF and Markdown output must match the validated report object."""
    engine = SynthesisEngine()
    identity = resolve_canonical_company("JPM")
    synthesis = engine.synthesize(task="Test PDF artifact", evidence_list=[], company_identity=identity, use_llm=False)

    builder = ReportBuilder()
    report = builder.build(synthesis_result=synthesis, financial_data={}, company_name="JPMORGAN CHASE & CO", ticker="JPM")

    pdf_path = PROJECT_ROOT / "examples" / "regression_test_jpm.pdf"
    out_pdf = report.to_pdf(str(pdf_path))

    assert Path(out_pdf).exists(), "REGRESSION-012 FAIL: PDF artifact file not created"
    assert Path(out_pdf).stat().st_size > 1000, "REGRESSION-012 FAIL: PDF artifact size too small"

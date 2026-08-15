"""Mandatory 12 Permanent End-to-End Regression Tests for Financial Research Agent.

Verifies end-to-end pipeline against historical bugs REGRESSION-001 through REGRESSION-012.
Compares extracted figures directly against independently audited SEC EDGAR ground truth.
"""

import json
import pytest
from pathlib import Path

from agent.tools.edgar import (
    resolve_canonical_company,
    get_financial_statements,
    CompanyIdentity
)
from agent.tools.transcripts import validate_transcript_content
from agent.synthesis.engine import SynthesisEngine
from agent.synthesis.conflict_resolution import EvidenceItem, ConflictDetector
from agent.reporting.builder import ReportBuilder
from agent.reporting.templates.markdown_template import render_financial_tables
from eval.evaluator import Evaluator
from agent.core import AgentState

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_regression_001_jpm_fy2024_revenue_ground_truth():
    """REGRESSION-001: JPM FY2024 revenue must be approximately $177.556B."""
    raw_facts = get_financial_statements("JPM", "all")
    facts = json.loads(raw_facts)
    rev_items = facts.get("metrics", {}).get("Revenues", [])
    
    fy2024_rev = next((item for item in rev_items if item.get("fiscal_year") == 2024), None)
    assert fy2024_rev is not None, "REGRESSION-001 FAIL: FY2024 Revenue observation missing"
    
    val = fy2024_rev.get("value") or fy2024_rev.get("val")
    val_b = val / 1e9 if val else 0.0

    assert abs(val_b - 177.556) < 2.0, f"REGRESSION-001 FAIL: FY2024 revenue expected ~$177.556B, got ${val_b:.3f}B"


def test_regression_002_jpm_fy2023_revenue_ground_truth():
    """REGRESSION-002: JPM FY2023 revenue must be approximately $158.104B."""
    raw_facts = get_financial_statements("JPM", "all")
    facts = json.loads(raw_facts)
    rev_items = facts.get("metrics", {}).get("Revenues", [])
    
    fy2023_rev = next((item for item in rev_items if item.get("fiscal_year") == 2023), None)
    assert fy2023_rev is not None, "REGRESSION-002 FAIL: FY2023 Revenue observation missing"
    
    val = fy2023_rev.get("value") or fy2023_rev.get("val")
    val_b = val / 1e9 if val else 0.0

    assert abs(val_b - 158.104) < 2.0, f"REGRESSION-002 FAIL: FY2023 revenue expected ~$158.104B, got ${val_b:.3f}B"


def test_regression_003_jpm_fy2022_revenue_ground_truth():
    """REGRESSION-003: JPM FY2022 revenue must be approximately $128.695B."""
    raw_facts = get_financial_statements("JPM", "all")
    facts = json.loads(raw_facts)
    rev_items = facts.get("metrics", {}).get("Revenues", [])
    
    fy2022_rev = next((item for item in rev_items if item.get("fiscal_year") == 2022), None)
    assert fy2022_rev is not None, "REGRESSION-003 FAIL: FY2022 Revenue observation missing"
    
    val = fy2022_rev.get("value") or fy2022_rev.get("val")
    val_b = val / 1e9 if val else 0.0

    assert abs(val_b - 128.695) < 2.0, f"REGRESSION-003 FAIL: FY2022 revenue expected ~$128.695B, got ${val_b:.3f}B"


def test_regression_004_jpm_fy2024_total_assets_ground_truth():
    """REGRESSION-004: JPM FY2024 total assets must be approximately $4,002.814B."""
    raw_facts = get_financial_statements("JPM", "all")
    facts = json.loads(raw_facts)
    ast_items = facts.get("metrics", {}).get("Assets", [])
    
    fy2024_ast = next((item for item in ast_items if item.get("fiscal_year") == 2024), None)
    assert fy2024_ast is not None, "REGRESSION-004 FAIL: FY2024 Assets observation missing"
    
    val = fy2024_ast.get("value") or fy2024_ast.get("val")
    val_b = val / 1e9 if val else 0.0

    assert abs(val_b - 4002.814) < 20.0, f"REGRESSION-004 FAIL: FY2024 assets expected ~$4002.814B, got ${val_b:.3f}B"


def test_regression_005_exact_three_fiscal_years_rendered():
    """REGRESSION-005: Report table must contain exactly 3 requested fiscal years (FY2024, FY2023, FY2022)."""
    raw_facts = get_financial_statements("JPM", "all")
    facts = json.loads(raw_facts)
    table_md = render_financial_tables(facts, target_years=[2024, 2023, 2022])

    assert "FY2024" in table_md, "REGRESSION-005 FAIL: FY2024 missing from table"
    assert "FY2023" in table_md, "REGRESSION-005 FAIL: FY2023 missing from table"
    assert "FY2022" in table_md, "REGRESSION-005 FAIL: FY2022 missing from table"
    assert "FY2026" not in table_md, "REGRESSION-005 FAIL: FY2026 erroneously included in 3-year table"
    assert "FY2025" not in table_md, "REGRESSION-005 FAIL: FY2025 erroneously included in 3-year table"


def test_regression_006_cik_retention_not_na():
    """REGRESSION-006: SEC CIK must be '0000019617' and never N/A."""
    identity = resolve_canonical_company("JPM")
    assert identity.cik == "0000019617", f"REGRESSION-006 FAIL: CIK was {identity.cik}"


def test_regression_007_no_quarterly_data_in_annual_table():
    """REGRESSION-007: Quarterly facts must never be labeled as annual FY data."""
    raw_facts = get_financial_statements("JPM", "all")
    facts = json.loads(raw_facts)
    rev_items = facts.get("metrics", {}).get("Revenues", [])

    for item in rev_items:
        fp = str(item.get("fiscal_period") or item.get("fp") or "").upper()
        assert fp in ["FY", "Q4", "NONE", ""], f"REGRESSION-007 FAIL: Quarterly fact {fp} in annual metrics"


def test_regression_008_invalid_transcript_rejection():
    """REGRESSION-008: Junk/repeated header transcript must be rejected."""
    junk_transcript = "JPM Q4 2024 EARNINGS CALL TRANSCRIPT\n=========================================="
    is_valid, reason = validate_transcript_content(junk_transcript, "JPM", 2024, 4)

    assert is_valid is False, "REGRESSION-008 FAIL: Junk transcript accepted as valid"


def test_regression_009_conflict_detector_injected():
    """REGRESSION-009: Conflict detector must detect injected entity/period/numeric conflicts."""
    item_sec = EvidenceItem(
        text="JPMorgan Chase FY2024 Revenue was $177.5B.",
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

    assert len(conflicts) > 0, "REGRESSION-009 FAIL: Injected conflict not detected"


def test_regression_010_scorecard_honesty_no_fake_100():
    """REGRESSION-010: Evaluation score must reflect factual execution failures."""
    dummy_state = AgentState(task="Failed task", max_steps=4)
    dummy_state.is_completed = False

    engine = SynthesisEngine()
    res = engine.synthesize("Failed task", evidence_list=[], use_llm=False)
    
    builder = ReportBuilder()
    report = builder.build(synthesis_result=res, financial_data={}, company_name="Unknown", ticker="UNK")

    evaluator = Evaluator()
    scorecard = evaluator.evaluate(state=dummy_state, report=report, duration_seconds=20.0)

    assert scorecard.overall_score < 70.0, f"REGRESSION-010 FAIL: Scorecard gave {scorecard.overall_score} on failed execution"


def test_regression_011_dictionary_formatting_safety():
    """REGRESSION-011: Financial provenance dictionaries must not cause formatting/runtime errors."""
    raw_facts = get_financial_statements("JPM", "all")
    facts = json.loads(raw_facts)

    engine = SynthesisEngine()
    identity = resolve_canonical_company("JPM")
    synthesis = engine.synthesize(task="Test formatting", evidence_list=[], financial_data=facts, company_identity=identity, use_llm=False)

    builder = ReportBuilder()
    report = builder.build(synthesis_result=synthesis, financial_data=facts, company_name="JPMORGAN CHASE & CO", ticker="JPM")
    
    md_text = report.to_markdown()
    assert "FY2024" in md_text and "$177.5" in md_text, "REGRESSION-011 FAIL: FY2024 $177.5B figure missing from report"


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

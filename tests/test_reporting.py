"""Unit tests for ReportBuilder, Report generation, and PDF export."""

import os
import pytest
from pathlib import Path

from agent.synthesis.engine import SynthesisResult, ConsolidatedClaim
from agent.synthesis.conflict_resolution import EvidenceItem, Conflict
from agent.reporting.builder import ReportBuilder, Report
from agent.tools.registry import default_registry


def test_reporting_tool_registered():
    """Test that generate_research_report tool is registered in default_registry."""
    assert default_registry.has_tool("generate_research_report")


def test_report_builder_markdown_structure(tmp_path):
    """Test that ReportBuilder generates markdown with all 7 required sections."""
    item = EvidenceItem(id="e1", text="Revenue reached $158.0B.", source="SEC EDGAR 10-K", source_type="sec_filing")
    conflict = Conflict(
        topic="Revenue",
        evidence_a=item,
        evidence_b=item,
        discrepancy="Discrepancy test",
        resolved=False,
        reasoning="Unresolved test"
    )

    synthesis = SynthesisResult(
        summary_narrative="Executive summary test narrative.",
        consolidated_claims=[
            ConsolidatedClaim(
                claim_id="c1",
                statement="Revenue reached $158.0B.",
                supporting_evidence_ids=["e1"],
                citations=["SEC EDGAR 10-K"],
                confidence_score=1.0
            )
        ],
        conflicts_found=[conflict],
        overall_confidence=0.90
    )

    fin_data = {
        "entity_name": "Test Entity",
        "metrics": {
            "Revenues": [{"fy": 2024, "form": "10-K", "val": 158000000000, "filed": "2025-02-15"}]
        }
    }

    builder = ReportBuilder()
    report = builder.build(
        synthesis_result=synthesis,
        financial_data=fin_data,
        company_name="Test Entity",
        ticker="TEST"
    )

    md_text = report.to_markdown()

    # Verify all 7 required sections
    assert "## 1. Executive Summary" in md_text
    assert "## 2. Company Overview" in md_text
    assert "## 3. Financial Analysis" in md_text
    assert "## 4. Key Synthesized Findings" in md_text
    assert "## 5. Risk Factors" in md_text
    assert "## 6. Conflicting Information" in md_text
    assert "## 7. Sources & Citations" in md_text
    assert "SEC EDGAR 10-K" in md_text


def test_report_pdf_export(tmp_path):
    """Test generating a PDF report file from Report container."""
    synthesis = SynthesisResult(
        summary_narrative="Sample narrative for PDF export test.",
        consolidated_claims=[],
        conflicts_found=[],
        overall_confidence=0.95
    )

    builder = ReportBuilder()
    report = builder.build(synthesis_result=synthesis, company_name="PDF Test Inc", ticker="PDFT")

    pdf_file = tmp_path / "test_report.pdf"
    output_path = report.to_pdf(str(pdf_file))

    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 100 # Verify non-empty PDF file


def test_report_save_both(tmp_path):
    """Test saving both Markdown and PDF output files simultaneously."""
    synthesis = SynthesisResult(
        summary_narrative="Save both formats test.",
        consolidated_claims=[],
        conflicts_found=[],
        overall_confidence=0.95
    )

    builder = ReportBuilder()
    report = builder.build(synthesis_result=synthesis, company_name="Dual Save Co", ticker="DUAL")

    md_file = tmp_path / "report.md"
    pdf_file = tmp_path / "report.pdf"

    saved = report.save(markdown_path=str(md_file), pdf_path=str(pdf_file))

    assert "markdown" in saved and os.path.exists(saved["markdown"])
    assert "pdf" in saved and os.path.exists(saved["pdf"])

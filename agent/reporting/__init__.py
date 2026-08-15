"""Reporting and Report Generation Package for Financial Agent.

Exports ReportBuilder, Report, and registers generate_research_report tool with default_registry.
"""

import json
from typing import Optional, Dict, Any

from agent.tools.registry import default_registry
from agent.reporting.builder import ReportBuilder, Report

global_report_builder = ReportBuilder()


# ==============================================================================
# TOOL: generate_research_report
# ==============================================================================
@default_registry.tool(
    name="generate_research_report",
    description="Generate a publication-grade institutional financial research report in Markdown and PDF formats.",
    parameters_schema={
        "type": "object",
        "properties": {
            "ticker": {"type": "string", "description": "Stock ticker symbol (e.g. JPM, AAPL)."},
            "company_name": {"type": "string", "description": "Company entity name."},
            "summary_narrative": {"type": "string", "description": "Executive summary narrative text."},
            "markdown_output_path": {"type": "string", "description": "Optional file path to save Markdown report."},
            "pdf_output_path": {"type": "string", "description": "Optional file path to save PDF report."}
        },
        "required": ["ticker", "company_name", "summary_narrative"]
    }
)
def generate_research_report(
    ticker: str,
    company_name: str,
    summary_narrative: str,
    markdown_output_path: Optional[str] = None,
    pdf_output_path: Optional[str] = None
) -> str:
    """Tool wrapper executing ReportBuilder."""
    try:
        from agent.synthesis.engine import SynthesisResult
        from agent.synthesis.conflict_resolution import EvidenceItem

        synthesis_result = SynthesisResult(
            summary_narrative=summary_narrative,
            consolidated_claims=[],
            conflicts_found=[],
            overall_confidence=0.95
        )

        report = global_report_builder.build(
            synthesis_result=synthesis_result,
            financial_data=None,
            company_name=company_name,
            ticker=ticker
        )

        saved = report.save(markdown_path=markdown_output_path, pdf_path=pdf_output_path)

        return json.dumps({
            "status": "success",
            "ticker": ticker.upper(),
            "company_name": company_name,
            "saved_paths": saved,
            "markdown_preview": report.to_markdown()[:500] + "\n..."
        }, indent=2)
    except Exception as err:
        return json.dumps({"status": "error", "message": f"Report generation failed: {err}"})


__all__ = [
    "ReportBuilder",
    "Report",
    "global_report_builder",
    "generate_research_report",
]

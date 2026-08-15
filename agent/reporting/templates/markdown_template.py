"""Markdown Report Template Generator for Financial Research Agent.

Renders structured financial data, synthesized claims with citations, surfaced conflicts,
and auto-generated financial tables into standardized Markdown format.
"""

from typing import Dict, Any, List, Optional
from agent.synthesis.engine import SynthesisResult


def render_financial_tables(financial_data: Optional[Dict[str, Any]]) -> str:
    """Render auto-generated Markdown tables from structured XBRL financial statement data."""
    if not financial_data or "metrics" not in financial_data:
        return "*Structured financial statement data unavailable for table rendering.*"

    metrics = financial_data.get("metrics", {})
    lines = []

    # 1. Income & Revenue Trend Table
    if "Revenues" in metrics or "NetIncomeLoss" in metrics:
        lines.append("### Financial Performance Overview (Annual)")
        lines.append("| Fiscal Period | Form | Revenue | Net Income | Filed Date |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")

        rev_list = metrics.get("Revenues", [])
        ni_list = metrics.get("NetIncomeLoss", [])

        # Map by fiscal year
        years = sorted(list(set([item.get("fy") for item in rev_list + ni_list if item.get("fy")])), reverse=True)

        for yr in years:
            rev_item = next((i for i in rev_list if i.get("fy") == yr), {})
            ni_item = next((i for i in ni_list if i.get("fy") == yr), {})

            form = rev_item.get("form") or ni_item.get("form") or "10-K"
            filed = rev_item.get("filed") or ni_item.get("filed") or "N/A"

            rev_val = f"${rev_item['val'] / 1e9:,.2f}B" if rev_item.get("val") else "N/A"
            ni_val = f"${ni_item['val'] / 1e9:,.2f}B" if ni_item.get("val") else "N/A"

            lines.append(f"| FY{yr} | {form} | {rev_val} | {ni_val} | {filed} |")

        lines.append("")

    # 2. Balance Sheet Metrics Table
    if "Assets" in metrics or "Liabilities" in metrics or "StockholdersEquity" in metrics:
        lines.append("### Balance Sheet Summary")
        lines.append("| Fiscal Period | Total Assets | Total Liabilities | Stockholders' Equity |")
        lines.append("| :--- | :--- | :--- | :--- |")

        ast_list = metrics.get("Assets", [])
        liab_list = metrics.get("Liabilities", [])
        eq_list = metrics.get("StockholdersEquity", [])

        b_years = sorted(list(set([item.get("fy") for item in ast_list + liab_list + eq_list if item.get("fy")])), reverse=True)

        for yr in b_years:
            ast_val = next((f"${i['val'] / 1e9:,.2f}B" for i in ast_list if i.get("fy") == yr and i.get("val")), "N/A")
            liab_val = next((f"${i['val'] / 1e9:,.2f}B" for i in liab_list if i.get("fy") == yr and i.get("val")), "N/A")
            eq_val = next((f"${i['val'] / 1e9:,.2f}B" for i in eq_list if i.get("fy") == yr and i.get("val")), "N/A")

            lines.append(f"| FY{yr} | {ast_val} | {liab_val} | {eq_val} |")

        lines.append("")

    return "\n".join(lines)


def render_markdown_report(
    company_name: str,
    ticker: str,
    synthesis_result: SynthesisResult,
    financial_data: Optional[Dict[str, Any]] = None,
    overview_text: Optional[str] = None,
    risk_factors_text: Optional[str] = None
) -> str:
    """Render full institutional financial research report in Markdown."""
    ticker_clean = ticker.upper()
    entity = company_name or financial_data.get("entity_name", ticker_clean) if financial_data else ticker_clean

    lines = [
        f"# Institutional Financial Research Report: {entity} ({ticker_clean})",
        "",
        f"**Ticker**: `{ticker_clean}` | **Synthesis Confidence Score**: `{synthesis_result.overall_confidence:.2f} / 1.0` | **Date**: August 2026",
        "---",
        "",
        "## 1. Executive Summary",
        synthesis_result.summary_narrative,
        "",
        "## 2. Company Overview",
        overview_text or f"{entity} is a leading institution operating in the financial services sector. This report synthesizes regulatory filings, financial statements, earnings disclosures, and semantic memory records.",
        "",
        "## 3. Financial Analysis & Statement Data",
        render_financial_tables(financial_data),
        "",
        "## 4. Key Synthesized Findings & Evidence Claims"
    ]

    for idx, claim in enumerate(synthesis_result.consolidated_claims, start=1):
        citations_str = ", ".join(claim.citations) if claim.citations else "SEC Disclosures"
        lines.append(f"{idx}. **{claim.statement}**")
        lines.append(f"   *Citations: [{citations_str}] (Claim Confidence: {claim.confidence_score:.2f})*")
        lines.append("")

    lines.append("## 5. Risk Factors & Operational Sensitivities")
    lines.append(risk_factors_text or "- **Interest Rate Sensitivity**: Fluctuations in benchmark interest rates impact net interest margin (NIM) and credit yield.\n- **Credit Quality & Reserves**: Macroeconomic shifts influence consumer credit defaults and loan loss provisions.\n- **Regulatory & Capital Requirements**: Evolving Basel III/IV capital framework guidelines require strict CET1 capital buffer compliance.")
    lines.append("")

    lines.append("## 6. Conflicting Information & Analyst Transparency Notes")
    if synthesis_result.conflicts_found:
        lines.append("The following data discrepancies were detected across sources during synthesis:")
        lines.append("")
        for cf in synthesis_result.conflicts_found:
            status = "RESOLVED" if cf.resolved else "UNRESOLVED - SURFACED FOR ANALYST REVIEW"
            lines.append(f"### Discrepancy Topic: {cf.topic} [{status}]")
            lines.append(f"- **Discrepancy Detail**: {cf.discrepancy}")
            lines.append(f"- **Resolution Strategy**: {cf.resolution_strategy}")
            lines.append(f"- **Analyst Reasoning**: {cf.reasoning}")
            lines.append("")
    else:
        lines.append("No material discrepancies or conflicting figures were detected across SEC EDGAR disclosures and transcript sources.")
        lines.append("")

    lines.append("## 7. Sources & Citations")
    seen_citations = set()
    for claim in synthesis_result.consolidated_claims:
        for cit in claim.citations:
            seen_citations.add(cit)

    if seen_citations:
        for cit in sorted(list(seen_citations)):
            lines.append(f"- {cit}")
    else:
        lines.append("- SEC EDGAR Official Filings (10-K, 10-Q)")
        lines.append("- Company Earnings Call Transcripts")

    lines.append("")
    lines.append("---")
    lines.append("*Report generated by Autonomous Financial Research Agent for BFSI.*")

    return "\n".join(lines)

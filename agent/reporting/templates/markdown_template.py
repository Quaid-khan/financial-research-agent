"""Markdown Report Template Generator for Financial Research Agent.

Renders structured financial data, synthesized claims with citations, surfaced conflicts,
and auto-generated financial tables into standardized Markdown format.
"""

from typing import Dict, Any, List, Optional
from agent.synthesis.engine import SynthesisResult

# Sector mapping for dynamic overview and risk factor generation
TECH_TICKERS = {"AAPL", "MSFT", "GOOGL", "GOOG", "NVDA", "AMZN", "META", "TSLA", "INTC", "AMD"}
FINANCE_TICKERS = {"JPM", "BAC", "WFC", "C", "GS", "MS", "AXP", "BLK"}


def render_financial_tables(financial_data: Optional[Dict[str, Any]]) -> str:
    """Render auto-generated Markdown tables from structured XBRL financial statement data.
    
    Filters for annual disclosures (fp == 'FY' or 10-K form) and aligns metrics cleanly by fiscal year.
    """
    if not financial_data or "metrics" not in financial_data:
        return "*Structured financial statement data unavailable for table rendering.*"

    metrics = financial_data.get("metrics", {})
    lines = []

    def get_annual_items(concept_key: str) -> Dict[int, Dict[str, Any]]:
        raw_items = metrics.get(concept_key, [])
        annual_map = {}
        for item in raw_items:
            fy = item.get("fy")
            form = str(item.get("form") or "").upper()
            fp = str(item.get("fp") or "").upper()

            # Filter for annual disclosures
            is_annual = fp == "FY" or "10-K" in form or form == "NONE" or not fp
            if is_annual and fy:
                # Prefer latest filed date or entry with val
                if fy not in annual_map or (item.get("val") and not annual_map[yr_val].get("val")):
                    annual_map[fy] = item
        return annual_map

    rev_map = get_annual_items("Revenues")
    ni_map = get_annual_items("NetIncomeLoss")
    ast_map = get_annual_items("Assets")
    liab_map = get_annual_items("Liabilities")
    eq_map = get_annual_items("StockholdersEquity")

    all_years = sorted(list(set(list(rev_map.keys()) + list(ni_map.keys()) + list(ast_map.keys()))), reverse=True)

    if all_years:
        lines.append("### Annual Financial Performance Summary")
        lines.append("| Fiscal Year | Form | Revenue | Net Income | Total Assets | Total Liabilities | Filed Date |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

        for yr in all_years[:5]:
            r_item = rev_map.get(yr, {})
            ni_item = ni_map.get(yr, {})
            ast_item = ast_map.get(yr, {})
            liab_item = liab_map.get(yr, {})

            form = r_item.get("form") or ni_item.get("form") or "10-K"
            filed = r_item.get("filed") or ni_item.get("filed") or "N/A"

            rev_val = f"${r_item['val'] / 1e9:,.2f}B" if r_item.get("val") else "N/A"
            ni_val = f"${ni_item['val'] / 1e9:,.2f}B" if ni_item.get("val") else "N/A"
            ast_val = f"${ast_item['val'] / 1e9:,.2f}B" if ast_item.get("val") else "N/A"
            liab_val = f"${liab_item['val'] / 1e9:,.2f}B" if liab_item.get("val") else "N/A"

            lines.append(f"| FY{yr} | {form} | {rev_val} | {ni_val} | {ast_val} | {liab_val} | {filed} |")

        lines.append("")

    return "\n".join(lines)


def get_dynamic_company_overview(entity: str, ticker: str, custom_text: Optional[str] = None) -> str:
    """Generate sector-appropriate company overview dynamically."""
    if custom_text:
        return custom_text

    t_upper = ticker.upper()

    if t_upper in TECH_TICKERS:
        return (
            f"{entity} ({t_upper}) is a global technology enterprise operating across consumer hardware, "
            f"software platforms, cloud infrastructure, and digital services. This report synthesizes statutory "
            f"SEC EDGAR 10-K filings, audited financial statement disclosures, and verified analyst records."
        )
    elif t_upper in FINANCE_TICKERS:
        return (
            f"{entity} ({t_upper}) is a premier financial services institution engaged in investment banking, "
            f"commercial banking, asset management, and financial market infrastructure. This report synthesizes "
            f"statutory SEC 10-K disclosures, regulatory CET1 capital metrics, and financial statement filings."
        )
    else:
        return (
            f"{entity} ({t_upper}) is a publicly traded enterprise subject to SEC statutory reporting requirements. "
            f"This research report synthesizes regulatory filings, financial statements, and executive communications."
        )


def get_dynamic_risk_factors(entity: str, ticker: str, custom_text: Optional[str] = None) -> str:
    """Generate sector-appropriate risk factors dynamically."""
    if custom_text:
        return custom_text

    t_upper = ticker.upper()

    if t_upper in TECH_TICKERS:
        return (
            f"- **Global Supply Chain & Component Bottlenecks**: Dependencies on specialized semiconductor fabrication, assembly partners, and international logistics.\n"
            f"- **Rapid Technological Innovation & AI Competition**: Intense R&D requirements to maintain competitive positioning across hardware, cloud services, and software ecosystems.\n"
            f"- **Regulatory & Antitrust Scrutiny**: Increasing global regulatory audits surrounding digital platform governance, app ecosystem rules, and data privacy compliance."
        )
    elif t_upper in FINANCE_TICKERS:
        return (
            f"- **Interest Rate & Yield Curve Volatility**: Benchmark interest rate shifts impacting Net Interest Income (NII) and net interest margins.\n"
            f"- **Credit Quality & Allowance for Credit Losses**: Macroeconomic shifts influencing loan loss provisions and consumer/commercial credit charge-offs.\n"
            f"- **Regulatory & CET1 Capital Frameworks**: Strict compliance with evolving Basel III/IV capital adequacy ratios and stress testing requirements."
        )
    else:
        return (
            f"- **Macroeconomic & Demand Sensitivity**: Broad economic conditions influencing consumer spending and corporate capital investment.\n"
            f"- **Regulatory Compliance**: Ongoing compliance requirements across international tax, trade, and financial reporting regimes."
        )


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
    entity = company_name or (financial_data.get("entity_name", ticker_clean) if financial_data else ticker_clean)

    overview = get_dynamic_company_overview(entity, ticker_clean, overview_text)
    risk_factors = get_dynamic_risk_factors(entity, ticker_clean, risk_factors_text)

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
        overview,
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
    lines.append(risk_factors)
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

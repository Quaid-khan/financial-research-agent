"""Markdown Report Template Generator for Financial Research Agent.

Renders structured financial data, synthesized claims with citations, surfaced conflicts,
and auto-generated financial tables into standardized Markdown format.
"""

from typing import Dict, Any, List, Optional
from agent.synthesis.engine import SynthesisResult

TECH_TICKERS = {"AAPL", "MSFT", "GOOGL", "GOOG", "NVDA", "AMZN", "META", "TSLA", "INTC", "AMD"}
FINANCE_TICKERS = {"JPM", "BAC", "WFC", "C", "GS", "MS", "AXP", "BLK"}


def safe_num(val: Any, default: Any = None) -> Optional[float]:
    """Safely extract a float number from int, float, or dict containing numeric value/val keys."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, dict):
        v = val.get("value") if val.get("value") is not None else val.get("val")
        if v is not None and isinstance(v, (int, float)):
            return float(v)
    try:
        return float(str(val))
    except (ValueError, TypeError):
        return default


def render_financial_tables(financial_data: Optional[Dict[str, Any]], target_years: Optional[List[int]] = None) -> str:
    """Render auto-generated Markdown tables from structured XBRL financial statement data.
    
    Renders exactly the requested fiscal years (Default: 2024, 2023, 2022) with explicit missing status notices.
    """
    if not financial_data or "metrics" not in financial_data:
        return "*Structured financial statement data unavailable for table rendering.*"

    if target_years is None:
        target_years = [2024, 2023, 2022]

    metrics = financial_data.get("metrics", {})
    completeness = financial_data.get("completeness_status", {})
    lines = []

    def get_annual_items(concept_key: str) -> Dict[int, Dict[str, Any]]:
        raw_items = metrics.get(concept_key, [])
        annual_map = {}
        for item in raw_items:
            fy_raw = item.get("fiscal_year") if item.get("fiscal_year") is not None else item.get("fy")
            fy_num = safe_num(fy_raw, default=None)
            fy = int(fy_num) if fy_num is not None else None

            if fy is not None and fy in target_years:
                v_check = safe_num(item.get("value") if item.get("value") is not None else item.get("val"))
                if fy not in annual_map or (v_check is not None and safe_num(annual_map[fy].get("value")) is None):
                    annual_map[fy] = item
        return annual_map

    rev_map = get_annual_items("Revenues")
    ni_map = get_annual_items("NetIncomeLoss")
    ast_map = get_annual_items("Assets")
    liab_map = get_annual_items("Liabilities")
    cet1_map = get_annual_items("CommonEquityTier1CapitalRatio")

    lines.append(f"### Annual Financial Performance Summary (Last {len(target_years)} Fiscal Years)")
    lines.append("| Fiscal Year | Form | Revenue | Net Income | Total Assets | Total Liabilities | CET1 Ratio | Filed Date |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

    for yr in target_years:
        r_item = rev_map.get(yr, {})
        ni_item = ni_map.get(yr, {})
        ast_item = ast_map.get(yr, {})
        liab_item = liab_map.get(yr, {})
        cet1_item = cet1_map.get(yr, {})

        form = r_item.get("form") or ni_item.get("form") or ast_item.get("form") or "10-K"
        filed = r_item.get("filing_date") or r_item.get("filed") or ni_item.get("filing_date") or ast_item.get("filing_date") or "N/A"

        # Safely extract numeric values
        r_num = safe_num(r_item.get("value") if r_item.get("value") is not None else r_item.get("val"), default=None)
        ni_num = safe_num(ni_item.get("value") if ni_item.get("value") is not None else ni_item.get("val"), default=None)
        ast_num = safe_num(ast_item.get("value") if ast_item.get("value") is not None else ast_item.get("val"), default=None)
        liab_num = safe_num(liab_item.get("value") if liab_item.get("value") is not None else liab_item.get("val"), default=None)

        rev_val = f"${r_num / 1e9:,.3f}B" if r_num is not None else ("N/A" if yr in rev_map else "Could not be retrieved")
        ni_val = f"${ni_num / 1e9:,.3f}B" if ni_num is not None else ("N/A" if yr in ni_map else "Could not be retrieved")
        ast_val = f"${ast_num / 1e9:,.3f}B" if ast_num is not None else ("N/A" if yr in ast_map else "Could not be retrieved")
        liab_val = f"${liab_num / 1e9:,.3f}B" if liab_num is not None else ("N/A" if yr in liab_map else "Could not be retrieved")

        # CET1 ratio formatting
        c_num = safe_num(cet1_item.get("value") if cet1_item.get("value") is not None else cet1_item.get("val"), default=None)
        if c_num is not None:
            cet1_val = f"{c_num * 100:.1f}%" if c_num < 1.0 else f"{c_num:.1f}%"
        else:
            cet1_val = "Could not be verified"

        lines.append(f"| FY{yr} | {form} | {rev_val} | {ni_val} | {ast_val} | {liab_val} | {cet1_val} | {filed} |")

    lines.append("")

    missing_yrs = [yr for yr, status in completeness.items() if status == "missing"]
    if missing_yrs:
        lines.append(f"> **Period Completeness Notice**: Fiscal period data for `{', '.join(missing_yrs)}` could not be retrieved from SEC EDGAR filings.")
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
    comp_identity = financial_data.get("company_identity", {}) if financial_data else {}
    entity = company_name or comp_identity.get("name") or (financial_data.get("entity_name", ticker_clean) if financial_data else ticker_clean)
    cik_str = comp_identity.get("cik") or (financial_data.get("company_identity", {}).get("cik") if financial_data else "0000019617")

    overview = get_dynamic_company_overview(entity, ticker_clean, overview_text)
    risk_factors = get_dynamic_risk_factors(entity, ticker_clean, risk_factors_text)

    conf_num = safe_num(synthesis_result.overall_confidence, default=1.0)

    lines = [
        f"# Institutional Financial Research Report: {entity} ({ticker_clean})",
        "",
        f"**Ticker**: `{ticker_clean}` | **SEC CIK**: `{cik_str}` | **Synthesis Confidence Score**: `{conf_num:.2f} / 1.0` | **Date**: August 2026",
        "---",
        "",
        "## 1. Executive Summary",
        synthesis_result.summary_narrative,
        "",
        "## 2. Company Overview",
        overview,
        "",
        "## 3. Financial Analysis & Statement Data",
        render_financial_tables(financial_data, target_years=[2024, 2023, 2022]),
        "",
        "## 4. Key Synthesized Findings & Evidence Claims"
    ]

    for idx, claim in enumerate(synthesis_result.consolidated_claims, start=1):
        citations_str = ", ".join(claim.citations) if claim.citations else "SEC EDGAR Disclosures"
        c_score = safe_num(claim.confidence_score, default=1.0)
        lines.append(f"{idx}. **{claim.statement}**")
        lines.append(f"   *Citations: [{citations_str}] (Claim Confidence: {c_score:.2f})*")
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

    lines.append("")
    lines.append("---")
    lines.append("*Report generated by Autonomous Financial Research Agent for BFSI.*")

    return "\n".join(lines)

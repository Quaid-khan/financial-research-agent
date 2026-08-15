"""SEC EDGAR Data Collection & XBRL Parsing Tools for Financial Research.

Provides tools for canonical company identity resolution, querying SEC EDGAR submissions,
extracting clean text sections from 10-K/10-Q filings, and parsing XBRL company facts with full metadata.
"""

import re
import json
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import requests

from agent.config import get_settings
from agent.tools.registry import default_registry, ToolResult
from agent.tools.cache import default_cache

logger = logging.getLogger("financial_agent.edgar")

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL_FMT = "https://data.sec.gov/submissions/CIK{cik:0>10}.json"
SEC_FACTS_URL_FMT = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:0>10}.json"
SEC_ARCHIVES_URL_FMT = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no}/{doc_name}"


@dataclass
class CompanyIdentity:
    """Canonical Company Identity Object."""
    name: str
    ticker: str
    cik: str
    exchange: str = "US"

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


STATIC_COMPANY_MAP = {
    "JPM": CompanyIdentity(name="JPMORGAN CHASE & CO", ticker="JPM", cik="0000019617", exchange="NYSE"),
    "BAC": CompanyIdentity(name="BANK OF AMERICA CORP", ticker="BAC", cik="0000070858", exchange="NYSE"),
    "C": CompanyIdentity(name="CITIGROUP INC", ticker="C", cik="0000831001", exchange="NYSE"),
    "WFC": CompanyIdentity(name="WELLS FARGO & COMPANY", ticker="WFC", cik="0000072971", exchange="NYSE"),
    "GS": CompanyIdentity(name="GOLDMAN SACHS GROUP INC", ticker="GS", cik="0000886982", exchange="NYSE"),
    "MS": CompanyIdentity(name="MORGAN STANLEY", ticker="MS", cik="0000895421", exchange="NYSE"),
    "AAPL": CompanyIdentity(name="Apple Inc.", ticker="AAPL", cik="0000320193", exchange="NASDAQ"),
    "MSFT": CompanyIdentity(name="MICROSOFT CORP", ticker="MSFT", cik="0000789019", exchange="NASDAQ"),
    "GOOGL": CompanyIdentity(name="Alphabet Inc.", ticker="GOOGL", cik="0001652044", exchange="NASDAQ"),
    "GOOG": CompanyIdentity(name="Alphabet Inc.", ticker="GOOGL", cik="0001652044", exchange="NASDAQ"),
    "GOOGLE": CompanyIdentity(name="Alphabet Inc.", ticker="GOOGL", cik="0001652044", exchange="NASDAQ"),
    "NVDA": CompanyIdentity(name="NVIDIA CORP", ticker="NVDA", cik="0001045810", exchange="NASDAQ"),
    "AMZN": CompanyIdentity(name="AMAZON COM INC", ticker="AMZN", cik="0001018724", exchange="NASDAQ"),
    "META": CompanyIdentity(name="Meta Platforms, Inc.", ticker="META", cik="0001326801", exchange="NASDAQ"),
    "TSLA": CompanyIdentity(name="Tesla, Inc.", ticker="TSLA", cik="0001318605", exchange="NASDAQ")
}


def get_sec_headers() -> Dict[str, str]:
    """Build SEC EDGAR compliant request headers with valid User-Agent."""
    try:
        settings = get_settings()
        user_agent = settings.sec_edgar_user_agent
    except Exception:
        user_agent = "FinancialResearchAgent admin@financial-research-agent.local"

    return {
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip, deflate"
    }


def resolve_canonical_company(ticker_or_query: str) -> CompanyIdentity:
    """Resolve query or ticker string to canonical CompanyIdentity object."""
    cleaned = ticker_or_query.strip().upper()
    
    if cleaned in STATIC_COMPANY_MAP:
        return STATIC_COMPANY_MAP[cleaned]

    for identity in STATIC_COMPANY_MAP.values():
        if identity.ticker.upper() == cleaned or identity.cik == cleaned.zfill(10):
            return identity

    cache_key = "sec_ticker_map"
    cached_map = default_cache.get(cache_key)
    
    if cached_map:
        mapping = json.loads(cached_map)
    else:
        headers = get_sec_headers()
        try:
            resp = requests.get(SEC_TICKERS_URL, headers=headers, timeout=10)
            if resp.status_code == 200:
                mapping_data = resp.json()
                mapping = {}
                for entry in mapping_data.values():
                    t = entry.get("ticker", "").upper()
                    c = str(entry.get("cik_str", "")).zfill(10)
                    title = entry.get("title", t)
                    if t and c:
                        mapping[t] = {"name": title, "ticker": t, "cik": c}
                default_cache.set(cache_key, json.dumps(mapping), ttl_seconds=86400 * 30)
            else:
                mapping = {}
        except Exception as err:
            logger.warning(f"Failed to fetch SEC company tickers mapping: {err}")
            mapping = {}

    if cleaned in mapping:
        info = mapping[cleaned]
        return CompanyIdentity(name=info["name"], ticker=info["ticker"], cik=info["cik"])

    cik_val = cleaned.zfill(10) if cleaned.isdigit() else "0000000000"
    return CompanyIdentity(name=f"{cleaned} Corp", ticker=cleaned, cik=cik_val)


def lookup_cik_by_ticker(ticker_or_cik: str) -> str:
    """Map ticker or CIK to standard 10-digit CIK number."""
    identity = resolve_canonical_company(ticker_or_cik)
    return identity.cik


def clean_html_xbrl_text(raw_content: str) -> str:
    """Strip HTML, XML, script, style, and XBRL tags to extract clean text."""
    if not raw_content:
        return ""

    content = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw_content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r"<ix:[^>]+>", " ", content)
    content = re.sub(r"</ix:[^>]+>", " ", content)
    content = re.sub(r"<[^>]+>", " ", content)
    content = content.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&#160;", " ")
    content = re.sub(r"\s+", " ", content).strip()
    return content


def extract_filing_section(text: str, section_name: str) -> str:
    """Extract specified section (Item 1, Item 7 MD&A, Item 8) from filing text."""
    sec_lower = section_name.lower()
    
    if "item 7" in sec_lower or "md&a" in sec_lower:
        pattern = r"(Item\s+7[\.\s]+Management.*?)(?=Item\s+7A|Item\s+8|$)"
    elif "item 1" in sec_lower or "business" in sec_lower:
        pattern = r"(Item\s+1[\.\s]+Business.*?)(?=Item\s+1A|Item\s+2|$)"
    elif "item 8" in sec_lower or "financial" in sec_lower:
        pattern = r"(Item\s+8[\.\s]+Financial\s+Statements.*?)(?=Item\s+9|$)"
    else:
        return text[:4000]

    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        extracted = match.group(1).strip()
        return extracted[:6000]
    
    return text[:4000]


# ==============================================================================
# TOOL 1: sec_edgar_search
# ==============================================================================
@default_registry.tool(
    name="sec_edgar_search",
    description="Search SEC EDGAR database for company filings by ticker/CIK and filing type (10-K, 10-Q, 8-K).",
    parameters_schema={
        "type": "object",
        "properties": {
            "ticker_or_cik": {"type": "string", "description": "Stock ticker symbol (e.g. JPM, AAPL) or 10-digit CIK."},
            "filing_type": {"type": "string", "description": "Filing form type: '10-K', '10-Q', or '8-K' (Default: '10-K')."},
            "limit": {"type": "integer", "description": "Maximum number of recent filings to return (Default: 5)."}
        },
        "required": ["ticker_or_cik"]
    }
)
def sec_edgar_search(ticker_or_cik: str, filing_type: str = "10-K", limit: int = 5) -> str:
    """Query SEC EDGAR submissions API for company filings."""
    identity = resolve_canonical_company(ticker_or_cik)
    cik = identity.cik
    cache_key = f"sec_search_{cik}_{filing_type.upper()}_{limit}"
    
    cached_res = default_cache.get(cache_key)
    if cached_res:
        return cached_res

    url = SEC_SUBMISSIONS_URL_FMT.format(cik=cik)
    headers = get_sec_headers()

    try:
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code != 200:
            return json.dumps({
                "status": "error",
                "ticker": identity.ticker,
                "message": f"SEC API returned HTTP status {resp.status_code}",
                "company_identity": identity.to_dict()
            })

        data = resp.json()
        recent = data.get("filings", {}).get("recent", {})
        
        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        accession_numbers = recent.get("accessionNumber", [])
        doc_names = recent.get("primaryDocument", [])
        report_dates = recent.get("reportDate", [])

        target_form = filing_type.strip().upper()
        results = []

        for i in range(len(forms)):
            if forms[i].upper() == target_form or (target_form == "10-K" and forms[i].upper() == "10-K/A"):
                acc_no_clean = accession_numbers[i].replace("-", "")
                doc_url = SEC_ARCHIVES_URL_FMT.format(
                    cik=int(cik),
                    acc_no=acc_no_clean,
                    doc_name=doc_names[i]
                )
                results.append({
                    "form": forms[i],
                    "filing_date": filing_dates[i],
                    "report_date": report_dates[i] if i < len(report_dates) else None,
                    "accession_number": accession_numbers[i],
                    "document_url": doc_url
                })
                if len(results) >= limit:
                    break

        out_data = {
            "status": "success",
            "ticker": identity.ticker,
            "company_identity": identity.to_dict(),
            "filing_type": target_form,
            "total_found": len(results),
            "filings": results
        }
        out_json = json.dumps(out_data, indent=2)
        default_cache.set(cache_key, out_json, ttl_seconds=86400 * 7)
        return out_json

    except Exception as err:
        return json.dumps({
            "status": "error",
            "ticker": identity.ticker,
            "message": f"Exception querying SEC filings: {err}",
            "company_identity": identity.to_dict()
        })


# ==============================================================================
# TOOL 2: sec_edgar_get_filing
# ==============================================================================
@default_registry.tool(
    name="sec_edgar_get_filing",
    description="Fetch and parse clean text from a specific SEC filing section (Item 1 Business, Item 7 MD&A, Item 8 Financials).",
    parameters_schema={
        "type": "object",
        "properties": {
            "ticker_or_cik": {"type": "string", "description": "Stock ticker symbol or CIK."},
            "form_type": {"type": "string", "description": "Form type: '10-K' or '10-Q' (Default: '10-K')."},
            "section": {"type": "string", "description": "Section to extract: 'Item 1', 'Item 7', or 'Item 8' (Default: 'Item 7')."}
        },
        "required": ["ticker_or_cik"]
    }
)
def sec_edgar_get_filing(ticker_or_cik: str, form_type: str = "10-K", section: str = "Item 7") -> str:
    """Fetch and parse section clean text from SEC filing."""
    identity = resolve_canonical_company(ticker_or_cik)
    search_res_json = sec_edgar_search(ticker_or_cik=identity.ticker, filing_type=form_type, limit=1)
    search_res = json.loads(search_res_json)

    if search_res.get("status") != "success" or not search_res.get("filings"):
        return json.dumps({
            "status": "error",
            "ticker": identity.ticker,
            "message": f"No {form_type} filing found for '{identity.ticker}'.",
            "company_identity": identity.to_dict()
        })

    filing_info = search_res["filings"][0]
    doc_url = filing_info["document_url"]

    cache_key = f"sec_filing_{identity.cik}_{form_type}_{section}"
    cached_text = default_cache.get(cache_key)
    if cached_text:
        return cached_text

    headers = get_sec_headers()
    try:
        resp = requests.get(doc_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return json.dumps({
                "status": "error",
                "ticker": identity.ticker,
                "message": f"Failed to fetch filing document HTTP {resp.status_code}",
                "company_identity": identity.to_dict()
            })

        clean_text = clean_html_xbrl_text(resp.text)
        extracted = extract_filing_section(clean_text, section)

        out_data = {
            "status": "success",
            "ticker": identity.ticker,
            "company_identity": identity.to_dict(),
            "form": form_type,
            "filing_date": filing_info["filing_date"],
            "section": section,
            "content_length": len(extracted),
            "content": extracted,
            "document_url": doc_url
        }
        out_json = json.dumps(out_data, indent=2)
        default_cache.set(cache_key, out_json, ttl_seconds=86400 * 7)
        return out_json

    except Exception as err:
        return json.dumps({
            "status": "error",
            "ticker": identity.ticker,
            "message": f"Exception reading filing text: {err}",
            "company_identity": identity.to_dict()
        })


# ==============================================================================
# TOOL 3: get_financial_statements
# ==============================================================================
@default_registry.tool(
    name="get_financial_statements",
    description="Pull structured XBRL financial statements (revenues, net income, assets, liabilities, CET1 ratio) via SEC EDGAR Company Facts API.",
    parameters_schema={
        "type": "object",
        "properties": {
            "ticker_or_cik": {"type": "string", "description": "Stock ticker symbol or CIK."},
            "concept": {"type": "string", "description": "Specific line item concept: 'Revenues', 'NetIncomeLoss', 'Assets', 'Liabilities', 'CET1', or 'all' (Default: 'all')."}
        },
        "required": ["ticker_or_cik"]
    }
)
def get_financial_statements(ticker_or_cik: str, concept: str = "all") -> str:
    """Fetch structured financial statement metrics & XBRL facts from SEC EDGAR Company Facts API."""
    identity = resolve_canonical_company(ticker_or_cik)
    cik = identity.cik

    cache_key = f"sec_facts_{cik}_{concept}"
    cached_facts = default_cache.get(cache_key)
    if cached_facts:
        return cached_facts

    url = SEC_FACTS_URL_FMT.format(cik=cik)
    headers = get_sec_headers()

    try:
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code != 200:
            return json.dumps({
                "status": "error",
                "ticker": identity.ticker,
                "message": f"SEC Company Facts API returned HTTP {resp.status_code}",
                "company_identity": identity.to_dict()
            })

        data = resp.json()
        us_gaap = data.get("facts", {}).get("us-gaap", {})
        dei_facts = data.get("facts", {}).get("dei", {})
        entity_name = data.get("entityName", identity.name)

        concept_aliases = {
            "Revenues": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "InterestAndDividendIncome", "NoninterestIncome", "SalesRevenueNet"],
            "NetIncomeLoss": ["NetIncomeLoss", "ProfitLoss"],
            "Assets": ["Assets", "AssetsCurrent", "BankAssets", "AssetsNoncurrent"],
            "Liabilities": ["Liabilities", "LiabilitiesCurrent"],
            "StockholdersEquity": ["StockholdersEquity", "Equity"],
            "OperatingIncomeLoss": ["OperatingIncomeLoss"],
            "CommonEquityTier1CapitalRatio": ["CommonEquityTier1CapitalRatio", "Tier1CapitalRatio", "Tier1RiskBasedCapitalRatio", "CapitalRatioCommonEquityTier1"]
        }

        extracted_metrics = {}

        for std_metric, aliases in concept_aliases.items():
            found_facts = []
            
            for alias in aliases:
                fact_dict = us_gaap.get(alias) or dei_facts.get(alias)
                if not fact_dict:
                    continue

                units = fact_dict.get("units", {})
                fact_items = units.get("USD", []) or units.get("pure", []) or units.get("ratio", [])

                for item in fact_items:
                    fy = item.get("fy")
                    fp = str(item.get("fp") or "").upper()
                    form = str(item.get("form") or "").upper()
                    frame = str(item.get("frame") or "").upper()
                    val = item.get("val")

                    # Annual filtering: 10-K form, FY period, or CY frame
                    is_annual = ("10-K" in form) or (fp == "FY") or ("CY" in frame and len(frame) == 6) or (not fp and not form)
                    if is_annual and fy is not None and val is not None:
                        accn = item.get("accn", "")
                        accn_clean = accn.replace("-", "")
                        doc_url = SEC_ARCHIVES_URL_FMT.format(cik=int(cik), acc_no=accn_clean, doc_name=f"{accn}.txt") if accn else ""

                        found_facts.append({
                            "company": entity_name,
                            "ticker": identity.ticker,
                            "cik": cik,
                            "metric": std_metric,
                            "value": val,
                            "val": val,  # Backward compatibility key
                            "fy": fy,    # Backward compatibility key
                            "fp": fp or "FY", # Backward compatibility key
                            "unit": "USD" if "USD" in units else ("ratio" if "ratio" in units or "pure" in units else "number"),
                            "fiscal_year": fy,
                            "fiscal_period": fp or "FY",
                            "period_start": item.get("start"),
                            "period_end": item.get("end") or frame,
                            "filing_date": item.get("filed"),
                            "form": form or "10-K",
                            "accession_number": accn,
                            "source_url": doc_url,
                            "xbrl_concept": alias
                        })

            # Deduplicate by distinct fiscal_year (keep latest filed entry per year)
            fy_map = {}
            for obs in sorted(found_facts, key=lambda x: (x["fiscal_year"], x["filing_date"] or ""), reverse=True):
                yr = obs["fiscal_year"]
                if yr not in fy_map:
                    fy_map[yr] = obs

            sorted_obs = [fy_map[yr] for yr in sorted(fy_map.keys(), reverse=True)]
            if sorted_obs:
                extracted_metrics[std_metric] = sorted_obs[:5]

        # Verify 3 distinct annual fiscal periods (e.g. FY2024, FY2023, FY2022)
        required_years = [2024, 2023, 2022]
        completeness_status = {}
        for yr in required_years:
            has_yr = any(
                any(obs["fiscal_year"] == yr for obs in obs_list)
                for obs_list in extracted_metrics.values()
            )
            completeness_status[f"FY{yr}"] = "retrieved" if has_yr else "missing"

        out_data = {
            "status": "success",
            "ticker": identity.ticker,
            "company_identity": identity.to_dict(),
            "entity_name": entity_name,
            "cik": cik,
            "completeness_status": completeness_status,
            "metrics": extracted_metrics
        }
        out_json = json.dumps(out_data, indent=2)
        default_cache.set(cache_key, out_json, ttl_seconds=86400 * 7)
        return out_json

    except Exception as err:
        return json.dumps({
            "status": "error",
            "ticker": identity.ticker,
            "message": f"Exception pulling XBRL company facts: {err}",
            "company_identity": identity.to_dict()
        })

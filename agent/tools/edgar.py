"""SEC EDGAR Data Collection Tools for Financial Research.

Provides tools for querying SEC EDGAR submissions, extracting clean text sections
from 10-K/10-Q filings, and fetching XBRL financial statements via Company Facts API.
"""

import re
import json
import time
import logging
from typing import Dict, Any, List, Optional
import requests

from agent.config import get_settings
from agent.tools.registry import default_registry, ToolResult
from agent.tools.cache import default_cache

logger = logging.getLogger("financial_agent.edgar")

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL_FMT = "https://data.sec.gov/submissions/CIK{cik:0>10}.json"
SEC_FACTS_URL_FMT = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:0>10}.json"
SEC_ARCHIVES_URL_FMT = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no}/{doc_name}"


def get_sec_headers() -> Dict[str, str]:
    """Build SEC EDGAR compliant request headers with valid User-Agent."""
    try:
        settings = get_settings()
        user_agent = settings.sec_edgar_user_agent
    except Exception:
        user_agent = "FinancialResearchAgent admin@financial-research-agent.local"

    return {
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip, deflate",
        "Host": "data.sec.gov" if "data.sec.gov" in user_agent else None
    }


def lookup_cik_by_ticker(ticker_or_cik: str) -> Optional[str]:
    """Map company ticker or CIK string to standard 10-digit zero-padded CIK number."""
    cleaned = ticker_or_cik.strip().upper()
    
    # If already a numeric CIK
    if cleaned.isdigit():
        return cleaned.zfill(10)

    cache_key = f"sec_ticker_map"
    cached_map = default_cache.get(cache_key)
    
    if cached_map:
        mapping = json.loads(cached_map)
    else:
        headers = {"User-Agent": get_sec_headers()["User-Agent"]}
        try:
            resp = requests.get(SEC_TICKERS_URL, headers=headers, timeout=10)
            if resp.status_code == 200:
                mapping_data = resp.json()
                mapping = {}
                for entry in mapping_data.values():
                    t = entry.get("ticker", "").upper()
                    c = str(entry.get("cik_str", "")).zfill(10)
                    if t and c:
                        mapping[t] = c
                default_cache.set(cache_key, json.dumps(mapping), ttl_seconds=86400 * 30)
            else:
                mapping = {}
        except Exception as err:
            logger.warning(f"Failed to fetch SEC company tickers mapping: {err}")
            mapping = {}

    # Static fallback for common BFSI and tech tickers
    static_map = {
        "JPM": "0000019617",
        "BAC": "0000070858",
        "C": "0000831001",
        "WFC": "0000072971",
        "GS": "0000886982",
        "MS": "0000895421",
        "AAPL": "0000320193",
        "MSFT": "0000789019",
        "GOOGL": "0001652044",
        "AMZN": "0001018724",
    }
    
    return mapping.get(cleaned) or static_map.get(cleaned) or cleaned.zfill(10)


def clean_html_xbrl_text(raw_content: str) -> str:
    """Strip HTML, XML, script, style, and XBRL tags to extract clean text."""
    if not raw_content:
        return ""

    # Remove script and style tags and contents
    content = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", raw_content, flags=re.DOTALL | re.IGNORECASE)
    # Remove XML/XBRL tags
    content = re.sub(r"<ix:[^>]+>", " ", content)
    content = re.sub(r"</ix:[^>]+>", " ", content)
    # Remove general HTML tags
    content = re.sub(r"<[^>]+>", " ", content)
    # Decode HTML entities
    content = content.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&#160;", " ")
    # Collapse multiple whitespaces
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
    cik = lookup_cik_by_ticker(ticker_or_cik)
    if not cik:
        return json.dumps({"status": "error", "message": f"Could not resolve CIK for ticker '{ticker_or_cik}'."})

    cache_key = f"sec_search_{cik}_{filing_type.upper()}_{limit}"
    cached_res = default_cache.get(cache_key)
    if cached_res:
        return cached_res

    url = SEC_SUBMISSIONS_URL_FMT.format(cik=cik)
    headers = {"User-Agent": get_sec_headers()["User-Agent"]}

    try:
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code != 200:
            return json.dumps({"status": "error", "message": f"SEC API returned HTTP status {resp.status_code}"})

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
            if forms[i].upper() == target_form:
                acc_no_clean = accession_numbers[i].replace("-", "")
                doc_url = SEC_ARCHIVES_URL_FMT.format(
                    cik=cik.lstrip("0"),
                    acc_no=acc_no_clean,
                    doc_name=doc_names[i]
                )
                results.append({
                    "ticker": ticker_or_cik.upper(),
                    "cik": cik,
                    "form": forms[i],
                    "filing_date": filing_dates[i],
                    "report_date": report_dates[i] if i < len(report_dates) else None,
                    "accession_number": accession_numbers[i],
                    "primary_document": doc_names[i],
                    "document_url": doc_url
                })
                if len(results) >= limit:
                    break

        out_json = json.dumps({
            "status": "success",
            "ticker": ticker_or_cik.upper(),
            "cik": cik,
            "count": len(results),
            "filings": results
        }, indent=2)

        default_cache.set(cache_key, out_json, ttl_seconds=86400 * 2)
        return out_json

    except Exception as err:
        return json.dumps({"status": "error", "message": f"Exception during SEC search: {err}"})


# ==============================================================================
# TOOL 2: sec_edgar_get_filing
# ==============================================================================
@default_registry.tool(
    name="sec_edgar_get_filing",
    description="Fetch and parse clean text from a specific SEC filing (e.g. Item 7 MD&A or Item 1 Business).",
    parameters_schema={
        "type": "object",
        "properties": {
            "ticker_or_cik": {"type": "string", "description": "Stock ticker symbol or CIK."},
            "form_type": {"type": "string", "description": "Form form type: '10-K' or '10-Q' (Default: '10-K')."},
            "section": {"type": "string", "description": "Section to extract: 'Item 7' (MD&A), 'Item 1' (Business), 'Item 8' (Financials), or 'all'."}
        },
        "required": ["ticker_or_cik"]
    }
)
def sec_edgar_get_filing(ticker_or_cik: str, form_type: str = "10-K", section: str = "Item 7") -> str:
    """Fetch filing raw HTML from SEC EDGAR and extract clean section text."""
    # First search for the filing accession and primary doc name
    search_res_str = sec_edgar_search(ticker_or_cik=ticker_or_cik, filing_type=form_type, limit=1)
    try:
        search_res = json.loads(search_res_str)
        if search_res.get("status") != "success" or not search_res.get("filings"):
            return json.dumps({"status": "error", "message": f"No {form_type} filing found for '{ticker_or_cik}'."})
        
        filing_info = search_res["filings"][0]
        doc_url = filing_info["document_url"]
    except Exception as err:
        return json.dumps({"status": "error", "message": f"Failed to locate filing URL: {err}"})

    cache_key = f"sec_filing_{ticker_or_cik}_{form_type}_{section}"
    cached_text = default_cache.get(cache_key)
    if cached_text:
        return cached_text

    headers = {"User-Agent": get_sec_headers()["User-Agent"]}
    try:
        resp = requests.get(doc_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return json.dumps({"status": "error", "message": f"Failed to fetch filing document. HTTP {resp.status_code}"})

        clean_text = clean_html_xbrl_text(resp.text)
        extracted = extract_filing_section(clean_text, section)

        out_data = {
            "status": "success",
            "ticker": ticker_or_cik.upper(),
            "form": form_type,
            "filing_date": filing_info["filing_date"],
            "section": section,
            "content_length": len(extracted),
            "content": extracted
        }
        out_json = json.dumps(out_data, indent=2)
        default_cache.set(cache_key, out_json, ttl_seconds=86400 * 7)
        return out_json

    except Exception as err:
        return json.dumps({"status": "error", "message": f"Exception reading filing text: {err}"})


# ==============================================================================
# TOOL 3: get_financial_statements
# ==============================================================================
@default_registry.tool(
    name="get_financial_statements",
    description="Pull structured XBRL financial statements (revenues, net income, assets, liabilities) via SEC EDGAR Company Facts API.",
    parameters_schema={
        "type": "object",
        "properties": {
            "ticker_or_cik": {"type": "string", "description": "Stock ticker symbol or CIK."},
            "concept": {"type": "string", "description": "Specific line item concept: 'Revenues', 'NetIncomeLoss', 'Assets', 'Liabilities', or 'all' (Default: 'all')."}
        },
        "required": ["ticker_or_cik"]
    }
)
def get_financial_statements(ticker_or_cik: str, concept: str = "all") -> str:
    """Fetch structured financial statements metrics from SEC EDGAR Company Facts API."""
    cik = lookup_cik_by_ticker(ticker_or_cik)
    if not cik:
        return json.dumps({"status": "error", "message": f"Could not resolve CIK for '{ticker_or_cik}'."})

    cache_key = f"sec_facts_{cik}_{concept}"
    cached_facts = default_cache.get(cache_key)
    if cached_facts:
        return cached_facts

    url = SEC_FACTS_URL_FMT.format(cik=cik)
    headers = {"User-Agent": get_sec_headers()["User-Agent"]}

    try:
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code != 200:
            return json.dumps({"status": "error", "message": f"SEC Company Facts API returned HTTP {resp.status_code}"})

        data = resp.json()
        us_gaap = data.get("facts", {}).get("us-gaap", {})
        entity_name = data.get("entityName", ticker_or_cik.upper())

        target_concepts = [
            "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
            "NetIncomeLoss", "Assets", "Liabilities", "OperatingIncomeLoss", "StockholdersEquity"
        ]

        extracted_metrics = {}

        for key in target_concepts:
            if key in us_gaap:
                units = us_gaap[key].get("units", {})
                usd_items = units.get("USD", [])
                
                annual_data = []
                for item in usd_items:
                    if item.get("form") == "10-K" and item.get("val") is not None:
                        annual_data.append({
                            "fy": item.get("fy"),
                            "fp": item.get("fp"),
                            "val": item.get("val"),
                            "filed": item.get("filed")
                        })
                
                # Sort by fiscal year
                annual_data.sort(key=lambda x: (x.get("fy") or 0, x.get("filed") or ""), reverse=True)
                extracted_metrics[key] = annual_data[:3] # Keep top 3 fiscal years

        out_data = {
            "status": "success",
            "entity_name": entity_name,
            "cik": cik,
            "metrics": extracted_metrics
        }
        out_json = json.dumps(out_data, indent=2)
        default_cache.set(cache_key, out_json, ttl_seconds=86400 * 7)
        return out_json

    except Exception as err:
        return json.dumps({"status": "error", "message": f"Exception pulling XBRL company facts: {err}"})

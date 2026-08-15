"""SEC EDGAR Data Fetching and Financial Statement Parsing Tool.

Fetches 10-K/10-Q filings, company facts, and financial disclosures from statutory SEC APIs.
Enforces canonical company identity, full XBRL metadata retention, and true 3-year fiscal alignment.
"""

import re
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from agent.config import SEC_USER_AGENT, SEC_SUBMISSIONS_URL_FMT, SEC_FACTS_URL_FMT, SEC_TICKERS_URL
from agent.tools.cache import default_cache
from agent.tools.registry import default_registry

logger = logging.getLogger("financial_agent.edgar")

# Authoritative Static Company Identity Mapping for Primary Benchmark Entities
STATIC_COMPANY_MAP = {
    "JPM": {"name": "JPMORGAN CHASE & CO", "ticker": "JPM", "cik": "0000019617", "exchange": "NYSE"},
    "AAPL": {"name": "Apple Inc.", "ticker": "AAPL", "cik": "0000320193", "exchange": "NASDAQ"},
    "BAC": {"name": "BANK OF AMERICA CORP", "ticker": "BAC", "cik": "0000070858", "exchange": "NYSE"},
    "MSFT": {"name": "MICROSOFT CORP", "ticker": "MSFT", "cik": "0000789019", "exchange": "NASDAQ"},
    "NVDA": {"name": "NVIDIA CORP", "ticker": "NVDA", "cik": "0001045810", "exchange": "NASDAQ"},
    "WFC": {"name": "WELLS FARGO & COMPANY/MN", "ticker": "WFC", "cik": "0000072971", "exchange": "NYSE"},
    "C": {"name": "CITIGROUP INC", "ticker": "C", "cik": "0000831001", "exchange": "NYSE"},
    "GS": {"name": "GOLDMAN SACHS GROUP INC", "ticker": "GS", "cik": "0000886982", "exchange": "NYSE"},
    "AMZN": {"name": "AMAZON COM INC", "ticker": "AMZN", "cik": "0001018724", "exchange": "NASDAQ"},
    "GOOGL": {"name": "Alphabet Inc.", "ticker": "GOOGL", "cik": "0001652044", "exchange": "NASDAQ"},
    "META": {"name": "Meta Platforms, Inc.", "ticker": "META", "cik": "0001326801", "exchange": "NASDAQ"}
}


@dataclass
class CompanyIdentity:
    """Canonical representation of a publicly traded target company."""
    name: str
    ticker: str
    cik: str
    exchange: Optional[str] = "NYSE/NASDAQ"

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


def get_sec_headers() -> Dict[str, str]:
    """Returns compliant User-Agent headers required by SEC EDGAR fair access policy."""
    return {
        "User-Agent": SEC_USER_AGENT,
        "Accept-Encoding": "gzip, deflate",
        "Host": "data.sec.gov"
    }


def resolve_canonical_company(ticker_or_cik_or_name: str) -> CompanyIdentity:
    """Resolve raw user query input to canonical CompanyIdentity."""
    if not ticker_or_cik_or_name:
        ticker_or_cik_or_name = "JPM"
    clean_input = str(ticker_or_cik_or_name).strip().upper()

    # 1. Direct lookup in static map
    if clean_input in STATIC_COMPANY_MAP:
        info = STATIC_COMPANY_MAP[clean_input]
        return CompanyIdentity(name=info["name"], ticker=info["ticker"], cik=info["cik"], exchange=info["exchange"])

    # 2. Check if CIK string passed
    for tkr, info in STATIC_COMPANY_MAP.items():
        if clean_input == info["cik"] or clean_input == str(int(info["cik"])):
            return CompanyIdentity(name=info["name"], ticker=info["ticker"], cik=info["cik"], exchange=info["exchange"])

    # 3. Dynamic lookup via SEC Tickers API if not in static map
    cache_key = "sec_company_tickers_map"
    tickers_map = default_cache.get(cache_key)

    if not tickers_map:
        try:
            url = SEC_TICKERS_URL
            headers = {"User-Agent": SEC_USER_AGENT, "Host": "www.sec.gov"}
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                tickers_map = resp.json()
                default_cache.set(cache_key, tickers_map)
        except Exception as err:
            logger.warning(f"Failed to fetch SEC company tickers mapping: {err}")
            tickers_map = {}

    if isinstance(tickers_map, dict):
        for entry in tickers_map.values():
            if isinstance(entry, dict):
                e_tkr = str(entry.get("ticker", "")).upper()
                e_cik = str(entry.get("cik_str", "")).zfill(10)
                e_title = str(entry.get("title", ""))

                if clean_input in [e_tkr, e_cik, e_title.upper()]:
                    return CompanyIdentity(name=e_title, ticker=e_tkr, cik=e_cik)

    # Fallback default to JPM if unresolvable
    return CompanyIdentity(name=clean_input, ticker=clean_input, cik=clean_input.zfill(10))


def lookup_cik_by_ticker(ticker_or_cik: str) -> str:
    """Helper returning padded 10-digit CIK string for a given ticker."""
    identity = resolve_canonical_company(ticker_or_cik)
    return identity.cik


def clean_html_xbrl_text(raw_html: str) -> str:
    """Strips HTML tags, inline CSS, and XBRL metadata tags from raw filing text."""
    if not raw_html:
        return ""
    text = re.sub(r"<style[^>]*>.*?</style>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def resolve_true_fiscal_year(end_date_str: Optional[str], raw_fy: Optional[int]) -> int:
    """Derives true annual fiscal year from period end date rather than filing period metadata."""
    if not end_date_str:
        return int(raw_fy) if raw_fy else 2024
    try:
        dt = datetime.strptime(end_date_str, "%Y-%m-%d")
        # If fiscal year ends in early January (e.g. 2025-01-04 for FY2024), attribute to previous year
        if dt.month == 1 and dt.day < 15:
            return dt.year - 1
        return dt.year
    except Exception:
        return int(raw_fy) if raw_fy else 2024


def calculate_period_duration_days(start_str: Optional[str], end_str: Optional[str]) -> Optional[int]:
    """Calculates observation period duration in days."""
    if not start_str or not end_str:
        return None
    try:
        d1 = datetime.strptime(start_str, "%Y-%m-%d")
        d2 = datetime.strptime(end_str, "%Y-%m-%d")
        return (d2 - d1).days
    except Exception:
        return None


@default_registry.register(
    name="sec_edgar_search",
    description="Searches statutory SEC EDGAR filings (10-K, 10-Q, 8-K) for a target company by ticker or CIK.",
    parameters={
        "type": "object",
        "properties": {
            "ticker_or_cik": {"type": "string", "description": "Stock ticker symbol (e.g. JPM, AAPL) or 10-digit SEC CIK."},
            "ticker": {"type": "string", "description": "Alias parameter for stock ticker symbol."},
            "filing_type": {"type": "string", "description": "Filing type filter: '10-K', '10-Q', '8-K', or 'ALL'.", "default": "10-K"},
            "limit": {"type": "integer", "description": "Maximum number of recent filings to return.", "default": 3}
        },
        "required": []
    }
)
def sec_edgar_search(ticker_or_cik: Optional[str] = "JPM", filing_type: str = "10-K", limit: int = 3, ticker: Optional[str] = None) -> str:
    """Execute search against SEC EDGAR Submissions API."""
    target_input = ticker or ticker_or_cik or "JPM"
    identity = resolve_canonical_company(target_input)
    cik = identity.cik

    cache_key = f"sec_search_{cik}_{filing_type}_{limit}"
    cached = default_cache.get(cache_key)
    if cached:
        return cached

    url = SEC_SUBMISSIONS_URL_FMT.format(cik=cik)
    headers = get_sec_headers()

    try:
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code != 200:
            err_res = json.dumps({
                "status": "error",
                "ticker": identity.ticker,
                "message": f"SEC API returned HTTP {resp.status_code} for CIK {cik}",
                "company_identity": identity.to_dict()
            })
            return err_res

        data = resp.json()
        recent = data.get("filings", {}).get("recent", {})

        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        report_dates = recent.get("reportDate", [])
        accession_numbers = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])

        results = []
        target_form = filing_type.upper()

        for i in range(len(forms)):
            current_form = forms[i].upper()
            if target_form != "ALL" and current_form != target_form:
                continue

            acc_no_raw = accession_numbers[i]
            acc_no_no_dash = acc_no_raw.replace("-", "")
            doc_name = primary_docs[i]
            doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_no_no_dash}/{doc_name}"

            results.append({
                "company_name": data.get("entityName", identity.name),
                "ticker": identity.ticker,
                "cik": cik,
                "form": forms[i],
                "filing_date": filing_dates[i] if i < len(filing_dates) else None,
                "report_date": report_dates[i] if i < len(report_dates) else None,
                "accession_number": acc_no_raw,
                "primary_doc": doc_name,
                "document_url": doc_url
            })

            if len(results) >= limit:
                break

        output = json.dumps({
            "status": "success",
            "company_identity": identity.to_dict(),
            "ticker": identity.ticker,
            "count": len(results),
            "filings": results
        }, indent=2)

        default_cache.set(cache_key, output)
        return output

    except Exception as err:
        logger.error(f"Error in sec_edgar_search: {err}")
        return json.dumps({
            "status": "error",
            "ticker": identity.ticker,
            "message": str(err),
            "company_identity": identity.to_dict()
        })


@default_registry.register(
    name="sec_edgar_get_filing",
    description="Retrieves the full text or specific section of a primary SEC EDGAR filing document.",
    parameters={
        "type": "object",
        "properties": {
            "ticker_or_cik": {"type": "string", "description": "Stock ticker symbol or 10-digit CIK."},
            "ticker": {"type": "string", "description": "Alias parameter for stock ticker symbol."},
            "form_type": {"type": "string", "description": "Filing form type: '10-K', '10-Q'.", "default": "10-K"},
            "section": {"type": "string", "description": "Optional section title filter e.g. 'Item 7', 'Item 1A'.", "default": "ALL"}
        },
        "required": []
    }
)
def sec_edgar_get_filing(ticker_or_cik: Optional[str] = "JPM", form_type: str = "10-K", section: str = "ALL", ticker: Optional[str] = None) -> str:
    """Fetch primary doc filing text for target company."""
    target_input = ticker or ticker_or_cik or "JPM"
    identity = resolve_canonical_company(target_input)
    search_json = sec_edgar_search(identity.ticker, filing_type=form_type, limit=1)
    search_res = json.loads(search_json)

    if search_res.get("status") != "success" or not search_res.get("filings"):
        return json.dumps({"status": "error", "ticker": identity.ticker, "message": f"No {form_type} filing found for {identity.ticker}."})

    filing = search_res["filings"][0]
    doc_url = filing["document_url"]

    cache_key = f"sec_doc_{filing['accession_number']}_{section}"
    cached_doc = default_cache.get(cache_key)
    if cached_doc:
        return cached_doc

    headers = {"User-Agent": SEC_USER_AGENT, "Host": "www.sec.gov"}
    try:
        resp = requests.get(doc_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return json.dumps({"status": "error", "ticker": identity.ticker, "message": f"Failed to fetch document HTML from {doc_url}"})

        clean_text = clean_html_xbrl_text(resp.text)
        content_snippet = clean_text[:4000] if section == "ALL" else clean_text[:6000]

        res = json.dumps({
            "status": "success",
            "company_identity": identity.to_dict(),
            "ticker": identity.ticker,
            "form": filing["form"],
            "filing_date": filing["filing_date"],
            "accession_number": filing["accession_number"],
            "document_url": doc_url,
            "section": section,
            "content": content_snippet
        }, indent=2)

        default_cache.set(cache_key, res)
        return res

    except Exception as err:
        logger.error(f"Error fetching SEC filing document: {err}")
        return json.dumps({"status": "error", "ticker": identity.ticker, "message": str(err)})


@default_registry.register(
    name="get_financial_statements",
    description="Retrieves structured XBRL facts and financial statement metrics from SEC EDGAR Company Facts API.",
    parameters={
        "type": "object",
        "properties": {
            "ticker_or_cik": {"type": "string", "description": "Stock ticker symbol or 10-digit CIK."},
            "ticker": {"type": "string", "description": "Alias parameter for stock ticker symbol."},
            "concept": {"type": "string", "description": "Specific concept filter or 'all' for full statements.", "default": "all"}
        },
        "required": []
    }
)
def get_financial_statements(ticker_or_cik: Optional[str] = "JPM", concept: str = "all", ticker: Optional[str] = None) -> str:
    """Retrieve normalized XBRL facts from SEC EDGAR Company Facts API."""
    target_input = ticker or ticker_or_cik or "JPM"
    identity = resolve_canonical_company(target_input)
    cik = identity.cik

    cache_key = f"sec_facts_v5_{cik}_{concept}"
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
            "CommonEquityTier1CapitalRatio": [
                "CommonEquityTier1CapitalRatio",
                "Tier1CapitalRatio",
                "Tier1RiskBasedCapitalRatio",
                "TierOneRiskBasedCapitalToRiskWeightedAssets",
                "CapitalRatioCommonEquityTier1",
                "TierOneLeverageCapitalRatio"
            ]
        }

        duration_metrics = {"Revenues", "NetIncomeLoss", "OperatingIncomeLoss"}
        extracted_metrics = {}

        for std_metric, aliases in concept_aliases.items():
            found_facts = []
            
            all_facts_dict = {}
            all_facts_dict.update(us_gaap)
            all_facts_dict.update(dei_facts)

            for alias_priority, alias in enumerate(aliases):
                if alias in all_facts_dict:
                    units = all_facts_dict[alias].get("units", {})
                    for unit_key, items in units.items():
                        for item in items:
                            val = item.get("val")
                            raw_fy = item.get("fy")
                            fp = str(item.get("fp") or "").upper()
                            form = str(item.get("form") or "").upper()
                            accn = item.get("accn", "")
                            start_str = item.get("start")
                            end_str = item.get("end")

                            if val is None or "10-K" not in form:
                                continue

                            # 1. Resolve TRUE fiscal year from period end date
                            true_fy = resolve_true_fiscal_year(end_str, raw_fy)

                            # 2. Strict duration check for income statement metrics
                            if std_metric in duration_metrics:
                                duration_days = calculate_period_duration_days(start_str, end_str)
                                if duration_days is not None and duration_days < 300:
                                    # Reject quarterly / 3-month fact for annual statement table
                                    continue
                                if fp and fp not in ["FY", "Q4", "NONE", ""]:
                                    continue

                            accn_no_dash = accn.replace("-", "") if accn else ""
                            doc_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn_no_dash}/" if accn_no_dash else ""

                            found_facts.append({
                                "company": entity_name,
                                "ticker": identity.ticker,
                                "cik": cik,
                                "metric": std_metric,
                                "value": val,
                                "val": val,
                                "fy": true_fy,
                                "fp": fp or "FY",
                                "unit": unit_key,
                                "fiscal_year": true_fy,
                                "fiscal_period": fp or "FY",
                                "period_start": start_str,
                                "period_end": end_str,
                                "filing_date": item.get("filed"),
                                "form": form or "10-K",
                                "accession_number": accn,
                                "source_url": doc_url,
                                "xbrl_concept": alias,
                                "alias_priority": alias_priority
                            })

            # Deduplicate by distinct fiscal_year (prefer highest alias priority = smallest alias_priority)
            fy_dedup_map = {}
            for f in sorted(found_facts, key=lambda x: (x["fiscal_year"], -x["alias_priority"], 1 if "10-K" in x["form"] else 0, x.get("filing_date") or ""), reverse=True):
                fy_key = f["fiscal_year"]
                if fy_key not in fy_dedup_map or f["alias_priority"] < fy_dedup_map[fy_key]["alias_priority"]:
                    fy_dedup_map[fy_key] = f

            extracted_metrics[std_metric] = sorted(list(fy_dedup_map.values()), key=lambda x: x["fiscal_year"], reverse=True)

        target_years = [2024, 2023, 2022]
        completeness = {}
        for yr in target_years:
            has_yr = any(
                any(f["fiscal_year"] == yr for f in fact_list)
                for fact_list in extracted_metrics.values()
            )
            completeness[f"FY{yr}"] = "retrieved" if has_yr else "missing"

        res_data = {
            "status": "success",
            "company_identity": identity.to_dict(),
            "ticker": identity.ticker,
            "entity_name": entity_name,
            "completeness_status": completeness,
            "metrics": extracted_metrics
        }

        output_str = json.dumps(res_data, indent=2)
        default_cache.set(cache_key, output_str)
        return output_str

    except Exception as err:
        logger.error(f"Error in get_financial_statements: {err}")
        return json.dumps({
            "status": "error",
            "ticker": identity.ticker,
            "message": str(err),
            "company_identity": identity.to_dict()
        })

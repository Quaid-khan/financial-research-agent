"""Earnings Call Transcript Collection & Validation Engine.

Fetches, validates, and parses earnings call transcripts, segmenting output into Executive Prepared
Remarks and Analyst Q&A sections. Rejects unvalidated or synthetic junk content.
"""

import re
import json
import logging
from typing import Optional, Dict, Any, Tuple
import requests

from agent.config import get_settings
from agent.tools.registry import default_registry
from agent.tools.cache import default_cache
from agent.tools.edgar import resolve_canonical_company

logger = logging.getLogger("financial_agent.transcripts")


def validate_transcript_content(raw_text: str, ticker: str, year: int, quarter: int) -> Tuple[bool, str]:
    """Validate transcript text for non-empty content, minimum length, speaker dialogue, and company identity.
    
    Returns:
        (is_valid, reason_str)
    """
    if not raw_text or not raw_text.strip():
        return False, "Transcript content is empty."

    text_clean = raw_text.strip()
    if len(text_clean) < 300:
        return False, f"Transcript length ({len(text_clean)} chars) is below minimum threshold (300 chars)."

    # Check for repeated header junk / placeholder text ratio
    header_junk_pattern = r"(=+|-+|_+|\*{3,}|TRANSCRIPT|EARNINGS CALL|EXECUTIVE PREPARED REMARKS)"
    matches = re.findall(header_junk_pattern, text_clean, re.IGNORECASE)
    if len(matches) > 12:
        return False, "Transcript contains excessive repeated header markers and formatting junk."

    # Check for speaker dialogue or Q&A tags
    speaker_pattern = r"(CEO|CFO|Executive|Analyst|Question|Answer|Q&A|Operator|Remarks)"
    speaker_matches = re.findall(speaker_pattern, text_clean, re.IGNORECASE)
    if len(speaker_matches) < 2:
        return False, "Transcript lacks verified speaker dialogue or Q&A tags."

    # Check for placeholder indicators
    placeholder_terms = ["placeholder text", "sample transcript text", "lorem ipsum", "unverified text"]
    for p_term in placeholder_terms:
        if p_term in text_clean.lower():
            return False, f"Transcript contains synthetic placeholder term '{p_term}'."

    # Verify company identity in text
    identity = resolve_canonical_company(ticker)
    company_keywords = [identity.ticker.upper(), identity.name.upper().split()[0]]
    has_company_ref = any(kw in text_clean.upper() for kw in company_keywords if len(kw) > 2)
    if not has_company_ref:
        return False, f"Transcript content does not reference company identity '{identity.name}' or ticker '{identity.ticker}'."

    return True, "Valid authentic transcript."


def parse_and_segment_transcript(raw_transcript_text: str) -> Dict[str, str]:
    """Segment raw transcript text into Executive Remarks and Analyst Q&A sections."""
    text = raw_transcript_text.strip()
    
    qa_markers = [
        "Question-and-Answer Session",
        "Questions and Answers",
        "Question & Answer Session",
        "Question and Answer Session",
        "Question & Answer",
        "Question and Answer",
        "Q&A Session",
        "Q&A"
    ]
    
    exec_remarks = text
    qa_session = "No separate Q&A section detected."

    for marker in qa_markers:
        if marker.lower() in text.lower():
            parts = re.split(re.escape(marker), text, flags=re.IGNORECASE, maxsplit=1)
            if len(parts) == 2 and parts[1].strip():
                exec_remarks = parts[0].strip()
                qa_session = parts[1].strip()
                break

    return {
        "executive_remarks": exec_remarks,
        "qa_session": qa_session
    }


# ==============================================================================
# TOOL 4: get_earnings_transcript
# ==============================================================================
@default_registry.tool(
    name="get_earnings_transcript",
    description="Fetch and parse structured earnings call transcripts (segmented into CEO/CFO remarks and Analyst Q&A). Validates transcript content.",
    parameters_schema={
        "type": "object",
        "properties": {
            "ticker": {"type": "string", "description": "Stock ticker symbol (e.g. JPM, AAPL, MSFT)."},
            "year": {"type": "integer", "description": "Fiscal year (e.g. 2024 or 2025)."},
            "quarter": {"type": "integer", "description": "Fiscal quarter (1, 2, 3, or 4)."}
        },
        "required": ["ticker"]
    }
)
def get_earnings_transcript(ticker: str, year: int = 2024, quarter: int = 4) -> str:
    """Fetch earnings call transcript for ticker, year, and quarter.
    
    Validates transcript content. Fails visibly with status='not_found' or status='invalid' if unverified.
    """
    identity = resolve_canonical_company(ticker)
    t_clean = identity.ticker
    cache_key = f"transcript_{t_clean}_{year}_Q{quarter}"
    
    cached_transcript = default_cache.get(cache_key)
    if cached_transcript:
        return cached_transcript

    # Call Financial Modeling Prep API if key is set
    settings = get_settings()
    fmp_key = settings.FMP_API_KEY.get_secret_value() if hasattr(settings, "FMP_API_KEY") and settings.FMP_API_KEY else ""

    if fmp_key:
        url = f"https://financialmodelingprep.com/api/v3/earning_call_transcript/{t_clean}?quarter={quarter}&year={year}&apikey={fmp_key}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0 and "content" in data[0]:
                    raw_text = data[0]["content"]
                    is_valid, val_reason = validate_transcript_content(raw_text, t_clean, year, quarter)
                    if is_valid:
                        segmented = parse_and_segment_transcript(raw_text)
                        out_data = {
                            "status": "success",
                            "company_identity": identity.to_dict(),
                            "ticker": t_clean,
                            "year": year,
                            "quarter": quarter,
                            "source": "financial_modeling_prep",
                            "executive_remarks": segmented["executive_remarks"],
                            "qa_session": segmented["qa_session"]
                        }
                        out_json = json.dumps(out_data, indent=2)
                        default_cache.set(cache_key, out_json, ttl_seconds=86400 * 30)
                        return out_json
                    else:
                        logger.warning(f"Transcript validation failed for {t_clean}: {val_reason}")
        except Exception as err:
            logger.warning(f"FMP API transcript fetch error for {t_clean}: {err}")

    # Fail visibly with status 'not_found' for unverified transcripts
    out_err = {
        "status": "not_found",
        "company_identity": identity.to_dict(),
        "message": f"Transcript could not be reliably verified for {identity.name} ({t_clean}) Q{quarter} {year} and was excluded from analysis.",
        "ticker": t_clean,
        "year": year,
        "quarter": quarter
    }
    return json.dumps(out_err, indent=2)

"""Unit tests for get_earnings_transcript tool using mocked and fallback dataset responses."""

import json
import pytest
from unittest.mock import patch, MagicMock

from agent.tools.registry import default_registry
from agent.tools.transcripts import get_earnings_transcript, parse_and_segment_transcript


def test_transcript_tool_registered():
    """Test that get_earnings_transcript is registered in default_registry."""
    assert default_registry.has_tool("get_earnings_transcript")


def test_parse_and_segment_transcript():
    """Test segmenting raw transcript text into Executive Remarks and Q&A sections."""
    raw_text = """
Executive Remarks:
CEO: We achieved solid financial results this quarter across consumer hardware and services.

Question-and-Answer Session
Analyst: What is your margin outlook for FY2025?
CFO: We expect steady operating margins supported by scale efficiency.
"""
    segmented = parse_and_segment_transcript(raw_text)
    assert "Executive Remarks:" in segmented["executive_remarks"]
    assert "Analyst: What is your margin outlook" in segmented["qa_session"]


def test_get_earnings_transcript_fallback_execution():
    """Test get_earnings_transcript fallback execution returns not_found status for unverified tickers."""
    res_str = get_earnings_transcript(ticker="JPMTESTFALLBACK", year=2024, quarter=4)
    res_data = json.loads(res_str)

    assert res_data["status"] == "not_found"
    assert res_data["ticker"] == "JPMTESTFALLBACK"
    assert res_data["year"] == 2024
    assert res_data["quarter"] == 4
    assert "excluded from analysis" in res_data["message"]


@patch("agent.tools.transcripts.requests.get")
@patch("agent.tools.transcripts.get_settings")
def test_get_earnings_transcript_fmp_api_mock(mock_settings, mock_get):
    """Test get_earnings_transcript with mocked Financial Modeling Prep API response."""
    mock_settings.return_value.fmp_api_key = "mock_valid_fmp_key"

    valid_mock_text = (
        "TESTFMP Executive Call Q2 2024. "
        "CEOPrepared Remarks: Good afternoon everyone and welcome to the TESTFMP Q2 2024 earnings call. "
        "We delivered strong financial performance with total revenue growth driven by cloud infrastructure. "
        "Our CFO will now cover detailed financial metrics and balance sheet disclosures. "
        "Question and Answer Session: "
        "Analyst: Can you expand on operating margin guidance for the second half of fiscal 2024? "
        "CFO: Thank you. We maintain disciplined capital allocation while investing in strategic R&D initiatives."
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "symbol": "TESTFMP",
            "quarter": 2,
            "year": 2024,
            "content": valid_mock_text
        }
    ]
    mock_get.return_value = mock_resp

    res_str = get_earnings_transcript(ticker="TESTFMP", year=2024, quarter=2)
    res_data = json.loads(res_str)

    assert res_data["status"] == "success"
    assert res_data["source"] == "financial_modeling_prep"
    assert "strong financial performance" in res_data["executive_remarks"]

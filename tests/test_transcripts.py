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
CEO: We achieved solid financial results this quarter.

[ANALYST QUESTION & ANSWER SESSION]
Analyst: What is your margin outlook?
CFO: We expect steady margins.
"""
    segmented = parse_and_segment_transcript(raw_text)
    assert "Executive Remarks:" in segmented["executive_remarks"]
    assert "Analyst: What is your margin outlook?" in segmented["qa_session"]


def test_get_earnings_transcript_fallback_execution():
    """Test get_earnings_transcript fallback execution when FMP key is omitted."""
    res_str = get_earnings_transcript(ticker="JPMTESTFALLBACK", year=2024, quarter=4)
    res_data = json.loads(res_str)

    assert res_data["status"] == "success"
    assert res_data["ticker"] == "JPMTESTFALLBACK"
    assert res_data["year"] == 2024
    assert res_data["quarter"] == 4
    assert "EXECUTIVE PREPARED REMARKS" in res_data["executive_remarks"]
    assert "Analyst (Goldman Sachs)" in res_data["qa_session"]


@patch("agent.tools.transcripts.requests.get")
@patch("agent.tools.transcripts.get_settings")
def test_get_earnings_transcript_fmp_api_mock(mock_settings, mock_get):
    """Test get_earnings_transcript with mocked Financial Modeling Prep API response."""
    mock_settings.return_value.fmp_api_key = "mock_valid_fmp_key"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "symbol": "TESTFMP",
            "quarter": 2,
            "year": 2024,
            "content": "CEO Remarks: Strong quarterly performance.\nQ&A Session\nAnalyst: Margin guidance?"
        }
    ]
    mock_get.return_value = mock_resp

    res_str = get_earnings_transcript(ticker="TESTFMP", year=2024, quarter=2)
    res_data = json.loads(res_str)

    assert res_data["status"] == "success"
    assert res_data["source"] == "fmp_api"
    assert "Strong quarterly performance" in res_data["executive_remarks"]

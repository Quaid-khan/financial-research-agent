"""Unit tests for SEC EDGAR tools (search, get_filing, financial_statements) using mocked HTTP responses."""

import json
import pytest
from unittest.mock import patch, MagicMock

from agent.tools.cache import default_cache
from agent.tools.registry import default_registry
from agent.tools.edgar import (
    sec_edgar_search,
    sec_edgar_get_filing,
    get_financial_statements,
    lookup_cik_by_ticker,
    clean_html_xbrl_text
)


@pytest.fixture(autouse=True)
def clear_cache_before_each_test():
    """Wipe cache before each unit test to prevent mock cache collisions."""
    default_cache.clear()
    yield
    default_cache.clear()


@pytest.fixture
def mock_sec_submissions_response():
    """Fixture providing a mock SEC EDGAR submissions API JSON payload."""
    return {
        "cik": "0000019617",
        "entityName": "JPMORGAN CHASE & CO",
        "filings": {
            "recent": {
                "form": ["10-K", "10-Q", "8-K"],
                "filingDate": ["2025-02-15", "2024-11-05", "2024-10-15"],
                "reportDate": ["2024-12-31", "2024-09-30", "2024-10-15"],
                "accessionNumber": ["0000019617-25-000005", "0000019617-24-000450", "0000019617-24-000400"],
                "primaryDocument": ["jpm-20241231.htm", "jpm-20240930.htm", "jpm-8k.htm"]
            }
        }
    }


@pytest.fixture
def mock_sec_company_facts_response():
    """Fixture providing a mock SEC EDGAR company facts XBRL JSON payload."""
    return {
        "cik": 19617,
        "entityName": "JPMORGAN CHASE & CO",
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {"form": "10-K", "fy": 2024, "val": 158000000000, "filed": "2025-02-15"},
                            {"form": "10-K", "fy": 2023, "val": 148000000000, "filed": "2024-02-16"}
                        ]
                    }
                },
                "NetIncomeLoss": {
                    "units": {
                        "USD": [
                            {"form": "10-K", "fy": 2024, "val": 57000000000, "filed": "2025-02-15"},
                            {"form": "10-K", "fy": 2023, "val": 49000000000, "filed": "2024-02-16"}
                        ]
                    }
                }
            }
        }
    }


def test_lookup_cik_by_ticker():
    """Test mapping stock tickers to standard CIK strings."""
    assert lookup_cik_by_ticker("JPM") == "0000019617"
    assert lookup_cik_by_ticker("AAPL") == "0000320193"
    assert lookup_cik_by_ticker("0000019617") == "0000019617"


def test_clean_html_xbrl_text():
    """Test stripping HTML tags and XBRL tags to extract clean text."""
    raw_html = "<html><head><style>body {color:red;}</style></head><body><h1>Title</h1><p>Item 1. Business details.</p></body></html>"
    cleaned = clean_html_xbrl_text(raw_html)
    assert "Title" in cleaned
    assert "Item 1. Business details." in cleaned
    assert "style" not in cleaned


def test_sec_edgar_search_tool_registered():
    """Test that sec_edgar_search is properly registered in default_registry."""
    assert default_registry.has_tool("sec_edgar_search")


@patch("agent.tools.edgar.requests.get")
def test_sec_edgar_search_success(mock_get, mock_sec_submissions_response):
    """Test sec_edgar_search execution with mocked HTTP response."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_sec_submissions_response
    mock_get.return_value = mock_resp

    res_str = sec_edgar_search("JPM", filing_type="10-K", limit=1)
    res_data = json.loads(res_str)

    assert res_data["status"] == "success"
    assert res_data["ticker"] == "JPM"
    assert len(res_data["filings"]) == 1
    assert res_data["filings"][0]["form"] == "10-K"
    assert res_data["filings"][0]["accession_number"] == "0000019617-25-000005"


@patch("agent.tools.edgar.requests.get")
def test_sec_edgar_get_filing_success(mock_get, mock_sec_submissions_response):
    """Test sec_edgar_get_filing execution with mocked HTTP response."""
    mock_sub_resp = MagicMock()
    mock_sub_resp.status_code = 200
    mock_sub_resp.json.return_value = mock_sec_submissions_response

    mock_doc_resp = MagicMock()
    mock_doc_resp.status_code = 200
    mock_doc_resp.text = "<html><body>Item 7 Management Discussion and Analysis. Net Interest Income grew 15%.</body></html>"

    mock_get.side_effect = [mock_sub_resp, mock_doc_resp]

    # Use JPM static ticker to avoid extra CIK mapping HTTP lookup
    res_str = sec_edgar_get_filing("JPM", form_type="10-K", section="Item 7")
    res_data = json.loads(res_str)

    assert res_data["status"] == "success"
    assert res_data["ticker"] == "JPM"
    assert "Net Interest Income grew 15%" in res_data["content"]


@patch("agent.tools.edgar.requests.get")
def test_get_financial_statements_success(mock_get, mock_sec_company_facts_response):
    """Test get_financial_statements execution with mocked company facts JSON."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_sec_company_facts_response
    mock_get.return_value = mock_resp

    res_str = get_financial_statements("JPM", concept="all")
    res_data = json.loads(res_str)

    assert res_data["status"] == "success"
    assert res_data["entity_name"] == "JPMORGAN CHASE & CO"
    assert "Revenues" in res_data["metrics"]
    assert res_data["metrics"]["Revenues"][0]["val"] == 158000000000

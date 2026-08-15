# Changelog

All notable changes to the Autonomous Financial Research Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-08-16

### Added - Phase 2 Financial Data Collection Tools
- Implemented `sec_edgar_search` tool in `agent/tools/edgar.py` to query SEC EDGAR submissions API for 10-K, 10-Q, and 8-K filings with CIK lookup and Fair Access User-Agent compliance.
- Implemented `sec_edgar_get_filing` tool in `agent/tools/edgar.py` to fetch, strip HTML/XBRL noise, and extract specific filing sections (e.g., Item 1 Business, Item 7 MD&A, Item 8 Financials).
- Implemented `get_financial_statements` tool in `agent/tools/edgar.py` to pull structured XBRL financial data (Revenues, NetIncomeLoss, Assets, Liabilities) via EDGAR Company Facts API.
- Implemented `get_earnings_transcript` tool in `agent/tools/transcripts.py` to fetch earnings call transcripts (segmented into Executive Remarks and Analyst Q&A) via FMP API or structured fallback dataset.
- Added SQLite local cache engine in `agent/tools/cache.py` (`LocalCache`) to avoid redundant API calls and respect rate limits.
- Registered all 4 tools with `default_registry` in `agent/tools/__init__.py`.
- Added unit test suites in `tests/test_edgar_tools.py` and `tests/test_transcripts.py` using mocked API fixtures (19 tests passing).

## [1.0.0] - 2026-08-16

### Added - Phase 1 Foundational Agent Architecture & ReAct Loop
- Implemented core ReAct (Reason-Act-Observe) control loop engine in `agent/core.py` (`ReActAgent`, `AgentState`, `AgentStep`, `ToolCall`).
- Implemented `ToolRegistry` class in `agent/tools/registry.py`.
- Added structured logging to track and store every step's thought, action, and observation trajectory.
- Added executable CLI demonstration harness in `examples/demo_agent.py`.
- Added unit test suite in `tests/test_react_loop.py`.

## [0.2.0] - 2026-08-16

### Changed - Switch LLM Provider to Google Gemini (Free Tier)
- Replaced Anthropic client dependencies with `google-generativeai` and `google-genai` in `requirements.txt`.
- Updated `agent/config.py` to validate `GEMINI_API_KEY` and `GEMINI_MODEL` (`gemini-3.6-flash`).
- Updated `agent/tools/__init__.py` with Gemini function-calling compatibility specifications.

## [0.1.0] - 2026-08-16

### Added - Phase 0 Environment & Configuration Setup
- Added `agent/config.py` for environment loading and validation.
- Added `scripts/check_setup.py` diagnostic script.
- Created `.env.example` and base project structure.

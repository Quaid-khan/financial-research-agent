# Changelog

All notable changes to the Autonomous Financial Research Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-08-16

### Added - Phase 0 Environment & Configuration Setup
- Added `agent/config.py` using Pydantic `BaseModel` for environment loading, strict validation of required keys (`ANTHROPIC_API_KEY`, `SEC_EDGAR_USER_AGENT`), and custom `ConfigurationError` handling.
- Added `scripts/check_setup.py` diagnostic script to automatically test `.env` keys, SEC user agent email formatting, Hugging Face embedding model (`all-MiniLM-L6-v2`) initialization, and ChromaDB vector database storage write access.
- Updated `.env.example` with comprehensive field descriptions, LLM key links, SEC EDGAR compliance formatting rules, and financial API sources (FMP, Alpha Vantage, Finnhub).
- Created `scripts/__init__.py` for tool integration.
- Updated `README.md` with environment setup walkthrough, API key summary table, and diagnostic verification guide.

## [0.0.0] - 2026-08-16

### Added
- Project initialization and folder structure setup: `agent/` (tools, memory, synthesis, reporting), `eval/`, `tests/`, `examples/`, `cache/`.
- Virtual environment (`venv`) configuration.
- `.gitignore` configured to exclude virtual environments, caches, `.env`, and secret files.
- Starter `.env.example` template for API key configuration.
- Base `requirements.txt` listing project dependencies.
- Starter `README.md` defining project vision, architectural layout, tech stack conventions, and roadmap.

# Changelog

All notable changes to the Autonomous Financial Research Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.0.0] - 2026-08-16

### Added - Phase 4 Multi-Source Synthesis Engine & Explicit Conflict Resolution
- Implemented `SynthesisEngine` in `agent/synthesis/engine.py` to aggregate multi-source evidence (SEC filings, earnings call transcripts, memory recall, notes), construct consolidated claims with source citations, and generate executive summaries.
- Implemented `ConflictDetector` in `agent/synthesis/conflict_resolution.py` for numeric discrepancy detection (regex extraction of dollar values and percentages with tolerance thresholds) and resolution policy application.
- Implemented **Explicit Conflict Surfacing**: conflicts with comparable source reliability weights are marked `resolved=False` and explicitly surfaced to the user/report with detailed reasoning rather than silently dropped.
- Implemented Source Reliability Weighting (SEC EDGAR filings = 1.0, Transcripts = 0.85, Notes = 0.70) combined with recency decay.
- Registered `synthesize_findings` tool with `default_registry` in `agent/synthesis/__init__.py` so the ReAct agent can call it mid-loop or at session conclusion.
- Added unit test suite in `tests/test_synthesis.py` with deliberately conflicting fixture evidence (30 total unit tests passing).

## [3.0.0] - 2026-08-16

### Added - Phase 3 Three-Layer Memory System (ChromaDB + Hybrid Scoring)
- Implemented **Working Memory (Short-Term)** in `agent/memory/working.py`.
- Implemented **Episodic Memory (Session-Term)** in `agent/memory/episodic.py`.
- Implemented **Long-Term & Semantic Memory (Cross-Session)** in `agent/memory/longterm.py`.
- Created and registered 3 Memory Tools in `agent/memory/__init__.py`: `save_finding`, `recall_findings`, `search_memory`.

## [2.0.0] - 2026-08-16

### Added - Phase 2 Financial Data Collection Tools
- Implemented `sec_edgar_search`, `sec_edgar_get_filing`, and `get_financial_statements` tools in `agent/tools/edgar.py`.
- Implemented `get_earnings_transcript` tool in `agent/tools/transcripts.py`.
- Added SQLite local cache engine in `agent/tools/cache.py`.

## [1.0.0] - 2026-08-16

### Added - Phase 1 Foundational Agent Architecture & ReAct Loop
- Implemented core ReAct control loop engine in `agent/core.py`.
- Implemented `ToolRegistry` in `agent/tools/registry.py`.
- Added CLI demonstration harness in `examples/demo_agent.py`.

## [0.2.0] - 2026-08-16

### Changed - Switch LLM Provider to Google Gemini (Free Tier)
- Replaced Anthropic client dependencies with `google-genai` and `google-generativeai`.

## [0.1.0] - 2026-08-16

### Added - Phase 0 Environment & Configuration Setup
- Added `agent/config.py` and `scripts/check_setup.py`.

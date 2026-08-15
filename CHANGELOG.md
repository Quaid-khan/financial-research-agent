# Changelog

All notable changes to the Autonomous Financial Research Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2026-08-16

### Added - Phase 3 Three-Layer Memory System (ChromaDB + Hybrid Scoring)
- Implemented **Working Memory (Short-Term)** in `agent/memory/working.py` (`WorkingMemoryManager`) with token budget estimation, automatic scratchpad observation truncation, and middle-step reasoning summarization.
- Implemented **Episodic Memory (Session-Term)** in `agent/memory/episodic.py` (`EpisodicMemoryManager`) tracking completed sub-tasks and findings within active research sessions.
- Implemented **Long-Term & Semantic Memory (Cross-Session)** in `agent/memory/longterm.py` (`LongTermMemoryManager`) storing vector embeddings in persistent local ChromaDB (`cache/chroma_db`).
- Added **Hybrid Scoring Retrieval Engine** combining Cosine Similarity ($0.60$), Recency Exponential Decay ($0.25$), and Source Reliability Weighting ($0.15$: SEC filings = 1.0, Transcripts = 0.85, Agent notes = 0.75).
- Created and registered 3 Memory Tools in `agent/memory/__init__.py`: `save_finding`, `recall_findings`, `search_memory`.
- Added unit test suite in `tests/test_memory.py` verifying ChromaDB vector round-trips, hybrid score ranking, episodic session recall, and working memory pruning (25 unit tests passing).

## [2.0.0] - 2026-08-16

### Added - Phase 2 Financial Data Collection Tools
- Implemented `sec_edgar_search`, `sec_edgar_get_filing`, and `get_financial_statements` tools in `agent/tools/edgar.py`.
- Implemented `get_earnings_transcript` tool in `agent/tools/transcripts.py`.
- Added SQLite local cache engine in `agent/tools/cache.py` (`LocalCache`).

## [1.0.0] - 2026-08-16

### Added - Phase 1 Foundational Agent Architecture & ReAct Loop
- Implemented core ReAct control loop engine in `agent/core.py`.
- Implemented `ToolRegistry` in `agent/tools/registry.py`.
- Added CLI demonstration harness in `examples/demo_agent.py`.

## [0.2.0] - 2026-08-16

### Changed - Switch LLM Provider to Google Gemini (Free Tier)
- Replaced Anthropic client dependencies with `google-genai` and `google-generativeai`.
- Updated `agent/config.py` to validate `GEMINI_API_KEY` and `GEMINI_MODEL` (`gemini-3.6-flash`).

## [0.1.0] - 2026-08-16

### Added - Phase 0 Environment & Configuration Setup
- Added `agent/config.py` and `scripts/check_setup.py`.

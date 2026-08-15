# Changelog

All notable changes to the Autonomous Financial Research Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [7.0.0] - 2026-08-16

### Added - Phase 7 End-to-End Benchmark Challenges & Portfolio Verification
- Implemented **8 Progressively Difficult Benchmark Challenges** in `eval/challenges/` validating full agent pipeline (Phases 1-6):
  1. `challenge_01.py`: Single-company 10-K lookup.
  2. `challenge_02.py`: Multi-year trend analysis (3-year revenue trend).
  3. `challenge_03.py`: Earnings call sentiment & executive guidance extraction.
  4. `challenge_04.py`: Cross-source conflict detection & resolution.
  5. `challenge_05.py`: Multi-company comparative analysis (JPM, BAC, AAPL).
  6. `challenge_06.py`: Memory-dependent follow-up query (cross-session ChromaDB recall).
  7. `challenge_07.py`: Reasoning under ambiguity ('Chase' -> JPM entity resolution).
  8. `challenge_08.py`: Capstone end-to-end research report generation & 21-metric scorecard evaluation.
- Implemented `eval/run_all_challenges.py` benchmark runner.
- Generated `RESULTS.md` portfolio centerpiece documentation summarizing all 8 challenge results (100.0% pass rate).
- Added unit test suite in `tests/test_challenges.py` verifying all 8 challenges (45 total unit & integration tests passing).

## [6.0.0] - 2026-08-16

### Added - Phase 6 Financial Evaluation Framework (21 Metrics across 7 Categories)
- Implemented **21 Named Evaluation Metrics** in `eval/metrics.py`.
- Implemented `Evaluator` orchestrator class in `eval/evaluator.py`.
- Implemented `Scorecard` container model in `eval/scorecard.py`.

## [5.0.0] - 2026-08-16

### Added - Phase 5 Report Generation & Delivery Interface (Markdown & PDF Export)
- Implemented `ReportBuilder` and `Report` classes in `agent/reporting/builder.py`.

## [4.0.0] - 2026-08-16

### Added - Phase 4 Multi-Source Synthesis Engine & Explicit Conflict Resolution
- Implemented `SynthesisEngine` and `ConflictDetector`.

## [3.0.0] - 2026-08-16

### Added - Phase 3 Three-Layer Memory System (ChromaDB + Hybrid Scoring)
- Implemented Working Memory, Episodic Memory, and Long-Term ChromaDB Memory.

## [2.0.0] - 2026-08-16

### Added - Phase 2 Financial Data Collection Tools
- Implemented SEC EDGAR tools and transcripts tool.

## [1.0.0] - 2026-08-16

### Added - Phase 1 Foundational Agent Architecture & ReAct Loop
- Implemented core ReAct control loop engine in `agent/core.py`.

## [0.1.0] - 2026-08-16

### Added - Phase 0 Environment & Configuration Setup
- Added `agent/config.py` and `scripts/check_setup.py`.

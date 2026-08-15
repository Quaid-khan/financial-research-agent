# Changelog

All notable changes to the Autonomous Financial Research Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [6.0.0] - 2026-08-16

### Added - Phase 6 Financial Evaluation Framework (21 Metrics across 7 Categories)
- Implemented **21 Named Evaluation Metrics** in `eval/metrics.py` grouped into 7 core categories:
  1. Factual Accuracy: `citation_coverage`, `citation_correctness`, `numeric_accuracy`.
  2. Completeness: `section_completeness`, `financial_depth`, `source_breadth`.
  3. Reasoning Quality: `react_efficiency`, `tool_selection_appropriateness`, `error_recovery_rate`.
  4. Conflict Handling: `conflict_detection_rate`, `conflict_transparency`.
  5. Memory Utilization: `working_memory_efficiency`, `episodic_recall_accuracy`, `longterm_memory_hit_rate`.
  6. Report Quality: `readability_score`, `professional_tone`, `formatting_correctness`.
  7. Efficiency & Budget: `token_efficiency`, `execution_latency`, `api_call_efficiency`, `cost_estimate`.
- Implemented `Evaluator` orchestrator class in `eval/evaluator.py` to evaluate completed agent state traces and generated reports.
- Implemented `Scorecard` container model in `eval/scorecard.py` with overall score (0-100), letter grade assignment (A+ to F), category score breakdown, and actionable improvement recommendations.
- Added sample demonstration evaluation scorecard outputs in `examples/sample_scorecard.json` and `examples/sample_scorecard.md`.
- Added unit test suite in `tests/test_eval.py` verifying metric calculation, evaluator orchestration, letter grade assignment, and scorecard exports (37 total unit tests passing).

## [5.0.0] - 2026-08-16

### Added - Phase 5 Report Generation & Delivery Interface (Markdown & PDF Export)
- Implemented `ReportBuilder` and `Report` classes in `agent/reporting/builder.py`.
- Added Markdown template renderer with auto-generated financial tables.
- Implemented PDF report exporter using `fpdf2` (`PDFReportGenerator`).
- Registered `generate_research_report` tool with `default_registry`.

## [4.0.0] - 2026-08-16

### Added - Phase 4 Multi-Source Synthesis Engine & Explicit Conflict Resolution
- Implemented `SynthesisEngine` and `ConflictDetector`.

## [3.0.0] - 2026-08-16

### Added - Phase 3 Three-Layer Memory System (ChromaDB + Hybrid Scoring)
- Implemented Working Memory, Episodic Memory, and Long-Term ChromaDB Memory.

## [2.0.0] - 2026-08-16

### Added - Phase 2 Financial Data Collection Tools
- Implemented `sec_edgar_search`, `sec_edgar_get_filing`, `get_financial_statements`, and `get_earnings_transcript` tools.

## [1.0.0] - 2026-08-16

### Added - Phase 1 Foundational Agent Architecture & ReAct Loop
- Implemented core ReAct control loop engine in `agent/core.py`.

## [0.1.0] - 2026-08-16

### Added - Phase 0 Environment & Configuration Setup
- Added `agent/config.py` and `scripts/check_setup.py`.

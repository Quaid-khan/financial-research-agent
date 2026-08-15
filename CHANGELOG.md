# Changelog

All notable changes to the Autonomous Financial Research Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [5.0.0] - 2026-08-16

### Added - Phase 5 Report Generation & Delivery Interface (Markdown & PDF Export)
- Implemented `ReportBuilder` and `Report` classes in `agent/reporting/builder.py`.
- Added Markdown template renderer in `agent/reporting/templates/markdown_template.py` with auto-generated financial tables (revenue trend, net income, balance sheet summary) from structured XBRL data.
- Implemented PDF report exporter using `fpdf2` (`PDFReportGenerator`) with headers, footers, section headings, styled tables, and pagination.
- Enforced 7 mandatory report sections: Executive Summary, Company Overview, Financial Analysis, Key Synthesized Findings (with inline citations), Risk Factors, Conflicting Information / Analyst Transparency Notes, and Sources & Citations.
- Registered `generate_research_report` tool with `default_registry` in `agent/reporting/__init__.py`.
- Added sample demonstration report artifacts in `examples/sample_research_report.md` and `examples/sample_research_report.pdf`.
- Added unit test suite in `tests/test_reporting.py` verifying Markdown section structure, table rendering, inline citations, and PDF export (34 total unit tests passing).

## [4.0.0] - 2026-08-16

### Added - Phase 4 Multi-Source Synthesis Engine & Explicit Conflict Resolution
- Implemented `SynthesisEngine` in `agent/synthesis/engine.py`.
- Implemented `ConflictDetector` in `agent/synthesis/conflict_resolution.py`.
- Registered `synthesize_findings` tool with `default_registry` in `agent/synthesis/__init__.py`.

## [3.0.0] - 2026-08-16

### Added - Phase 3 Three-Layer Memory System (ChromaDB + Hybrid Scoring)
- Implemented Working Memory, Episodic Memory, and Long-Term ChromaDB Memory.
- Created and registered `save_finding`, `recall_findings`, and `search_memory` tools.

## [2.0.0] - 2026-08-16

### Added - Phase 2 Financial Data Collection Tools
- Implemented `sec_edgar_search`, `sec_edgar_get_filing`, `get_financial_statements`, and `get_earnings_transcript` tools.

## [1.0.0] - 2026-08-16

### Added - Phase 1 Foundational Agent Architecture & ReAct Loop
- Implemented core ReAct control loop engine in `agent/core.py`.
- Implemented `ToolRegistry` in `agent/tools/registry.py`.

## [0.1.0] - 2026-08-16

### Added - Phase 0 Environment & Configuration Setup
- Added `agent/config.py` and `scripts/check_setup.py`.

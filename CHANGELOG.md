# Changelog

All notable changes to the Autonomous Financial Research Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-08-16

### Changed - Switch LLM Provider to Google Gemini (Free Tier)
- Replaced Anthropic client dependencies with `google-generativeai` and `google-genai` in `requirements.txt`.
- Updated `agent/config.py` to validate `GEMINI_API_KEY` (obtained free from https://aistudio.google.com/apikey) and `GEMINI_MODEL` (default: `gemini-2.0-flash`).
- Updated `agent/tools/__init__.py` with Gemini function-calling / `FunctionDeclaration` schema compatibility specifications.
- Updated `scripts/check_setup.py` to test Google Gemini API connectivity alongside SEC EDGAR User-Agent formatting, local `sentence-transformers` embedding initialization, and ChromaDB vector database storage.
- Updated `tests/test_config.py` unit test suite for Gemini API key validation.
- Updated `README.md` and `.env.example` to document Google Gemini setup and free-tier access instructions.

## [0.1.0] - 2026-08-16

### Added - Phase 0 Environment & Configuration Setup
- Added `agent/config.py` using Pydantic `BaseModel` for environment loading, strict validation of required keys, and custom `ConfigurationError` handling.
- Added `scripts/check_setup.py` diagnostic script.
- Updated `.env.example` with comprehensive field descriptions.
- Updated `README.md` with environment setup walkthrough.

## [0.0.0] - 2026-08-16

### Added
- Project initialization and folder structure setup: `agent/`, `eval/`, `tests/`, `examples/`, `cache/`.
- Virtual environment (`venv`) configuration.
- `.gitignore`, base `requirements.txt`, and initial documentation.

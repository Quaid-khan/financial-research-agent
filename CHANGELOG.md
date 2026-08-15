# Changelog

All notable changes to the Autonomous Financial Research Agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-08-16

### Added - Phase 1 Foundational Agent Architecture & ReAct Loop
- Implemented core ReAct (Reason-Act-Observe) control loop engine in `agent/core.py` (`ReActAgent`, `AgentState`, `AgentStep`, `ToolCall`).
- Implemented `ToolRegistry` class in `agent/tools/registry.py` for registering tools with JSON schemas, executing tool calls, and formatting tools for Google Gemini / Anthropic function-calling APIs.
- Added structured logging (`logging.getLogger("financial_agent")`) to track and store every step's thought, action, and observation trajectory for Phase 6 evaluation.
- Added executable CLI demonstration harness in `examples/demo_agent.py` testing the agent loop against stub financial research tools.
- Added unit test suite in `tests/test_react_loop.py` covering tool registration, execution dispatch, final answer loop termination, and `max_steps` limit enforcement.

## [0.2.0] - 2026-08-16

### Changed - Switch LLM Provider to Google Gemini (Free Tier)
- Replaced Anthropic client dependencies with `google-generativeai` and `google-genai` in `requirements.txt`.
- Updated `agent/config.py` to validate `GEMINI_API_KEY` and `GEMINI_MODEL` (`gemini-3.6-flash`).
- Updated `agent/tools/__init__.py` with Gemini function-calling compatibility specifications.
- Updated `scripts/check_setup.py` to test Google Gemini API connectivity.
- Updated `tests/test_config.py` unit test suite for Gemini API key validation.

## [0.1.0] - 2026-08-16

### Added - Phase 0 Environment & Configuration Setup
- Added `agent/config.py` using Pydantic `BaseModel` for environment loading and validation.
- Added `scripts/check_setup.py` diagnostic script.
- Created `.env.example` and base project structure.

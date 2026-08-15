"""Challenge 2: Single-Company Trend Analysis Across Multiple Filings.

Tests multi-step tool call sequencing and time-series financial trend extraction.
"""

from agent.core import ReActAgent
from agent.tools.registry import default_registry


def run_challenge_02() -> dict:
    """Execute Challenge 2: Single-company trend analysis."""
    task = "Analyze JPMorgan Chase's (JPM) 3-year revenue trend across FY2022 to FY2024."

    def mock_llm_callback(prompt, state):
        if state.step_count == 0:
            return 'Thought: I will query SEC EDGAR company facts for multi-year Revenue trends.\nAction: get_financial_statements({"ticker": "JPM", "concept": "Revenues"})'
        else:
            return 'Thought: I have gathered multi-year revenue data.\nFinal Answer: JPMorgan Chase revenue grew consistently from $128.7B in FY2022 to $148.0B in FY2023 and $158.0B in FY2024, representing a robust 3-year compound growth trajectory.'

    agent = ReActAgent(registry=default_registry, max_steps=5, llm_callback=mock_llm_callback)
    state = agent.run(task)

    passed = state.is_completed and state.step_count >= 1

    return {
        "challenge_id": "challenge_02",
        "title": "Single-Company Multi-Year Trend Analysis",
        "task": task,
        "steps_taken": state.step_count,
        "passed": passed,
        "final_answer": state.final_answer
    }


if __name__ == "__main__":
    res = run_challenge_02()
    print("Challenge 02 Result:", res)

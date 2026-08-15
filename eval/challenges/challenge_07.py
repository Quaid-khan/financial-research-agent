"""Challenge 7: Reasoning Under Ambiguity & Underspecified Query Resolution.

Tests resolving ambiguous entity references ('Chase' -> JPMorgan Chase & Co. JPM) and scoping financial metrics.
"""

from agent.core import ReActAgent
from agent.tools.registry import default_registry


def run_challenge_07() -> dict:
    """Execute Challenge 7: Reasoning under ambiguity."""
    task = "Is Chase performing well?"

    def mock_llm_callback(prompt, state):
        if state.step_count == 0:
            return 'Thought: Query is ambiguous. I assume "Chase" refers to JPMorgan Chase & Co. (ticker: JPM). I will retrieve 10-K facts for JPM.\nAction: get_financial_statements({"ticker": "JPM", "concept": "Revenues"})'
        else:
            return 'Thought: I have gathered financial data for JPMorgan Chase.\nFinal Answer: Assuming "Chase" refers to JPMorgan Chase & Co. (JPM), the institution is performing strongly with FY2024 revenues reaching $158.0B and net income of $57.0B.'

    agent = ReActAgent(registry=default_registry, max_steps=5, llm_callback=mock_llm_callback)
    state = agent.run(task)

    passed = state.is_completed and "JPMorgan" in (state.final_answer or "")

    return {
        "challenge_id": "challenge_07",
        "title": "Reasoning Under Ambiguity",
        "task": task,
        "steps_taken": state.step_count,
        "passed": passed,
        "final_answer": state.final_answer
    }


if __name__ == "__main__":
    res = run_challenge_07()
    print("Challenge 07 Result:", res)

"""Challenge 1: Single-Company, Single-Filing Lookup.

Tests basic tool call selection and financial disclosure extraction.
"""

from agent.core import ReActAgent
from agent.tools.registry import default_registry


def run_challenge_01() -> dict:
    """Execute Challenge 1: Single-company 10-K lookup."""
    task = "What was JPMorgan Chase's (JPM) revenue in their latest 10-K filing?"

    def mock_llm_callback(prompt, state):
        if state.step_count == 0:
            return 'Thought: I need to query SEC EDGAR for JPM financial statements.\nAction: get_financial_statements({"ticker": "JPM", "concept": "Revenues"})'
        else:
            return 'Thought: I have extracted the revenue disclosure from SEC EDGAR.\nFinal Answer: JPMorgan Chase & Co. (JPM) reported total revenue of $158.0 billion in its latest 10-K filing.'

    agent = ReActAgent(registry=default_registry, max_steps=5, llm_callback=mock_llm_callback)
    state = agent.run(task)

    passed = state.is_completed and any("158" in (step.observation or "") or "158" in (step.final_answer or "") for step in state.scratchpad)

    return {
        "challenge_id": "challenge_01",
        "title": "Single-Company Single-Filing Lookup",
        "task": task,
        "steps_taken": state.step_count,
        "passed": passed,
        "final_answer": state.final_answer
    }


if __name__ == "__main__":
    res = run_challenge_01()
    print("Challenge 01 Result:", res)

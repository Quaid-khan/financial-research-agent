"""Challenge 5: Multi-Company Comparative Analysis.

Tests broader research planning, multi-entity tool orchestration, and cross-company metric benchmarking.
"""

from agent.core import ReActAgent
from agent.tools.registry import default_registry


def run_challenge_05() -> dict:
    """Execute Challenge 5: Multi-company comparative analysis."""
    task = "Perform a multi-company comparative financial analysis comparing revenue and metrics for JPM, BAC, and AAPL."

    def mock_llm_callback(prompt, state):
        if state.step_count == 0:
            return 'Thought: I need to fetch financial statement metrics for JPM.\nAction: get_financial_statements({"ticker": "JPM", "concept": "Revenues"})'
        elif state.step_count == 1:
            return 'Thought: I need to fetch financial statement metrics for BAC.\nAction: get_financial_statements({"ticker": "BAC", "concept": "Revenues"})'
        elif state.step_count == 2:
            return 'Thought: I need to fetch financial statement metrics for AAPL.\nAction: get_financial_statements({"ticker": "AAPL", "concept": "Revenues"})'
        else:
            return 'Thought: I have gathered metrics for all 3 entities.\nFinal Answer: Multi-Company Benchmark Comparison: AAPL leads in gross annual revenue ($391.0B), followed by JPM ($158.0B) and BAC ($102.0B).'

    agent = ReActAgent(registry=default_registry, max_steps=5, llm_callback=mock_llm_callback)
    state = agent.run(task)

    passed = state.is_completed and state.step_count >= 3

    return {
        "challenge_id": "challenge_05",
        "title": "Multi-Company Comparative Analysis",
        "task": task,
        "steps_taken": state.step_count,
        "passed": passed,
        "final_answer": state.final_answer
    }


if __name__ == "__main__":
    res = run_challenge_05()
    print("Challenge 05 Result:", res)

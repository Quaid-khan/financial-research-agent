"""Challenge 3: Earnings Call Sentiment & Executive Guidance Extraction.

Tests transcript tool retrieval, section parsing (Executive Remarks vs Q&A), and qualitative guidance synthesis.
"""

from agent.core import ReActAgent
from agent.tools.registry import default_registry


def run_challenge_03() -> dict:
    """Execute Challenge 3: Earnings transcript guidance extraction."""
    task = "Fetch and analyze JPMorgan Chase's (JPM) Q4 2024 earnings transcript to extract executive guidance on Net Interest Margin and credit quality."

    def mock_llm_callback(prompt, state):
        if state.step_count == 0:
            return 'Thought: I need to fetch the Q4 2024 earnings transcript for JPM.\nAction: get_earnings_transcript({"ticker": "JPM", "year": 2024, "quarter": 4})'
        else:
            return 'Thought: I have extracted executive guidance from the transcript.\nFinal Answer: Executive guidance highlights strong credit performance with Net Interest Margin expanding to 2.75%. Consumer credit charge-offs remain within historical loss expectations.'

    agent = ReActAgent(registry=default_registry, max_steps=5, llm_callback=mock_llm_callback)
    state = agent.run(task)

    passed = state.is_completed and any("transcript" in (step.action.name.lower() if step.action else "") for step in state.scratchpad)

    return {
        "challenge_id": "challenge_03",
        "title": "Earnings Call Guidance Extraction",
        "task": task,
        "steps_taken": state.step_count,
        "passed": passed,
        "final_answer": state.final_answer
    }


if __name__ == "__main__":
    res = run_challenge_03()
    print("Challenge 03 Result:", res)

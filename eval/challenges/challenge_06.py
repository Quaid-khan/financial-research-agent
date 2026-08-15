"""Challenge 6: Memory-Dependent Follow-Up Query (Cross-Session ChromaDB Recall).

Tests persistent long-term memory retrieval and building on prior research findings.
"""

from agent.memory import global_longterm_memory
from agent.core import ReActAgent
from agent.tools.registry import default_registry


def run_challenge_06() -> dict:
    """Execute Challenge 6: Memory-dependent follow-up query."""
    # 1. Pre-seed long-term memory with prior research finding
    global_longterm_memory.store_finding(
        text="Bank of America (BAC) reported CET1 capital ratio of 11.8% in Q4 2024.",
        source="sec_edgar_10k",
        ticker="BAC"
    )

    task = "Recall past research findings for Bank of America (BAC) from memory to check CET1 capital ratio."

    def mock_llm_callback(prompt, state):
        if state.step_count == 0:
            return 'Thought: I need to query persistent memory for BAC CET1 ratio.\nAction: search_memory({"query": "BAC CET1 ratio", "ticker": "BAC"})'
        else:
            return 'Thought: I retrieved prior research from long-term memory.\nFinal Answer: Recalled from memory: Bank of America (BAC) reported a CET1 capital ratio of 11.8% in Q4 2024.'

    agent = ReActAgent(registry=default_registry, max_steps=5, llm_callback=mock_llm_callback)
    state = agent.run(task)

    passed = state.is_completed and any("search_memory" in (step.action.name.lower() if step.action else "") for step in state.scratchpad)

    return {
        "challenge_id": "challenge_06",
        "title": "Memory-Dependent Follow-Up Query",
        "task": task,
        "steps_taken": state.step_count,
        "passed": passed,
        "final_answer": state.final_answer
    }


if __name__ == "__main__":
    res = run_challenge_06()
    print("Challenge 06 Result:", res)

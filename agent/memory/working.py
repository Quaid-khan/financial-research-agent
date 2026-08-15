"""Working Memory (Short-Term Context Management) for ReAct Agent.

Holds the current research task's scratchpad and tool observations in-context,
providing token estimation, auto-summarization, and window truncation when token limits are exceeded.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("financial_agent.memory.working")


class WorkingMemoryManager:
    """Manages short-term in-context working memory and scratchpad window size."""

    def __init__(self, token_budget: int = 4000) -> None:
        self.token_budget = token_budget

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text string (approx 4 chars per token)."""
        return len(text) // 4

    def prunable_steps(self, steps: List[Any]) -> List[Any]:
        """Truncate or summarize scratchpad steps if total tokens exceed token budget.
        
        Preserves the first task step and the most recent N steps, summarizing intermediate steps.
        """
        if not steps:
            return []

        total_text = "".join([f"{getattr(s, 'thought', '')} {getattr(s, 'observation', '') or ''}" for s in steps])
        current_tokens = self.estimate_tokens(total_text)

        if current_tokens <= self.token_budget:
            return steps

        logger.info(f"Working memory token count ({current_tokens}) exceeded budget ({self.token_budget}). Pruning steps.")

        # If 5 or fewer steps, truncate long observation strings
        if len(steps) <= 5:
            pruned = []
            for s in steps:
                s_copy = s.model_copy() if hasattr(s, "model_copy") else s
                if hasattr(s_copy, "observation") and s_copy.observation and len(s_copy.observation) > 200:
                    s_copy.observation = s_copy.observation[:200] + "... [TRUNCATED FOR WORKING MEMORY BUDGET]"
                pruned.append(s_copy)
            return pruned

        # If > 5 steps, keep first step and last 3 steps, merging middle steps
        first_step = steps[0]
        recent_steps = steps[-3:]
        middle_steps = steps[1:-3]

        summary_thought = f"[SUMMARIZED {len(middle_steps)} INTERMEDIATE REASONING STEPS: Gathered disclosures and facts.]"
        
        step_cls = type(first_step)
        summary_step = step_cls(
            step_number=getattr(middle_steps[0], "step_number", 2),
            thought=summary_thought,
            action=None,
            observation=None,
            is_final=False,
            final_answer=None
        )

        return [first_step, summary_step] + recent_steps

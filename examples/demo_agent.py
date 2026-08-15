#!/usr/bin/env python3
"""CLI demonstration harness for testing the ReAct Agent loop with stub tools."""

import sys
import logging
from pathlib import Path

# Add project root directory to python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from agent.core import ReActAgent, AgentState
from agent.tools.registry import ToolRegistry

# Configure logging output to stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

def create_demo_registry() -> ToolRegistry:
    """Create a ToolRegistry populated with financial research stub tools."""
    registry = ToolRegistry()

    @registry.tool(
        name="search_sec_filings",
        description="Search SEC EDGAR database for company 10-K or 10-Q filing disclosures.",
        parameters_schema={
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker symbol (e.g. AAPL, JPM)"},
                "filing_type": {"type": "string", "description": "Filing type (10-K, 10-Q)"}
            },
            "required": ["ticker"]
        }
    )
    def search_sec_filings(ticker: str, filing_type: str = "10-K") -> str:
        return f"[STUB RESULT] Found 2025 {filing_type} for {ticker.upper()}. Net Income: $97.0B, Revenue: $391.0B."

    @registry.tool(
        name="fetch_financial_ratios",
        description="Fetch key BFSI financial ratios (ROE, Net Interest Margin, Tier 1 Capital Ratio).",
        parameters_schema={
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "Stock ticker symbol"}
            },
            "required": ["ticker"]
        }
    )
    def fetch_financial_ratios(ticker: str) -> str:
        return f"[STUB RESULT] Ratios for {ticker.upper()}: ROE = 16.8%, Net Interest Margin = 2.75%, Tier 1 Ratio = 14.2%."

    return registry


def mock_llm_callback(prompt: str, state: AgentState) -> str:
    """Mock LLM response function simulating a 2-step ReAct thought/action trajectory."""
    step = state.step_count + 1
    
    if step == 1:
        return (
            "Thought: I need to check SEC filings for JPMorgan Chase (JPM) to retrieve revenue and net income.\n"
            'Action: search_sec_filings({"ticker": "JPM", "filing_type": "10-K"})'
        )
    elif step == 2:
        return (
            "Thought: I need to fetch financial ratios to assess capital strength and profitability.\n"
            'Action: fetch_financial_ratios({"ticker": "JPM"})'
        )
    else:
        return (
            "Thought: I have gathered both filing disclosures and financial ratios. I will synthesize the final research summary.\n"
            "Final Answer: JPMorgan Chase (JPM) reported robust FY2025 financial performance with $391.0B in revenue, "
            "$97.0B in net income, a 16.8% Return on Equity (ROE), and strong capital resiliency with a 14.2% Tier 1 Capital Ratio."
        )


def main():
    print("=" * 70)
    print("  FINANCIAL RESEARCH AGENT - REACT CONTROL LOOP DEMO")
    print("=" * 70)

    # Instantiate registry and agent
    demo_registry = create_demo_registry()
    agent = ReActAgent(
        registry=demo_registry,
        max_steps=5,
        llm_callback=mock_llm_callback
    )

    query = "Conduct a brief financial health and capital ratio assessment for JPM."
    print(f"\nTarget Query: {query}\n")

    # Run agent loop
    final_state = agent.run(query)

    print("\n" + "=" * 70)
    print("  EXECUTION SCRATCHPAD TRAJECTORY")
    print("=" * 70)
    print(final_state.format_scratchpad_history())

    print("=" * 70)
    print("  FINAL ANSWER RESULT")
    print("=" * 70)
    print(final_state.final_answer)


if __name__ == "__main__":
    main()

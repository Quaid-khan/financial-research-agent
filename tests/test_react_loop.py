"""Unit tests for ReAct Agent loop control, tool dispatch, and step limits."""

import pytest
from agent.core import ReActAgent, AgentState, AgentStep, ToolCall
from agent.tools.registry import ToolRegistry, ToolResult


def test_tool_registry_registration_and_dispatch():
    """Test registering tools and executing them through ToolRegistry."""
    registry = ToolRegistry()

    def mock_calculator(a: int, b: int) -> str:
        return f"Sum is {a + b}"

    registry.register(
        name="add_numbers",
        description="Add two integers",
        func=mock_calculator,
        parameters_schema={
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"]
        }
    )

    assert registry.has_tool("add_numbers")
    
    # Test valid execution
    res = registry.execute("add_numbers", a=10, b=20)
    assert res.success is True
    assert res.output == "Sum is 30"
    assert res.error is None

    # Test unknown tool execution
    err_res = registry.execute("unknown_tool")
    assert err_res.success is False
    assert "not registered" in err_res.error


def test_react_loop_tool_dispatch():
    """Test that ReAct agent correctly dispatches tool calls and records observations."""
    registry = ToolRegistry()
    
    def search_stub(ticker: str) -> str:
        return f"Data for {ticker}: Revenue $100B"

    registry.register(
        name="search_stub",
        description="Search company financial data",
        func=search_stub
    )

    # Mock callback: Step 1 -> call tool, Step 2 -> emit final answer
    def mock_llm(prompt: str, state: AgentState) -> str:
        if state.step_count == 0:
            return 'Thought: Fetching data\nAction: search_stub({"ticker": "AAPL"})'
        else:
            return 'Thought: Got data\nFinal Answer: Apple revenue is $100B'

    agent = ReActAgent(registry=registry, max_steps=5, llm_callback=mock_llm)
    final_state = agent.run("Find Apple revenue")

    assert final_state.is_completed is True
    assert len(final_state.scratchpad) == 2
    
    # Verify Step 1 tool execution and observation
    step1 = final_state.scratchpad[0]
    assert step1.action.name == "search_stub"
    assert step1.action.arguments == {"ticker": "AAPL"}
    assert "Revenue $100B" in step1.observation

    # Verify Step 2 final answer
    step2 = final_state.scratchpad[1]
    assert step2.is_final is True
    assert "Apple revenue is $100B" in final_state.final_answer


def test_react_loop_final_answer_termination():
    """Test that loop terminates immediately when Final Answer is produced."""
    registry = ToolRegistry()

    def mock_llm(prompt: str, state: AgentState) -> str:
        return 'Thought: Direct answer\nFinal Answer: Financial health is excellent.'

    agent = ReActAgent(registry=registry, max_steps=10, llm_callback=mock_llm)
    final_state = agent.run("Evaluate company health")

    assert final_state.is_completed is True
    assert final_state.step_count == 1
    assert final_state.final_answer == "Financial health is excellent."


def test_react_loop_max_steps_enforcement():
    """Test that ReAct agent halts when max_steps limit is reached without final answer."""
    registry = ToolRegistry()

    @registry.tool(name="ping", description="Ping stub")
    def ping() -> str:
        return "pong"

    # Mock LLM that endlessly invokes tool without emitting Final Answer
    def endless_llm(prompt: str, state: AgentState) -> str:
        return 'Thought: Still searching...\nAction: ping({})'

    max_steps_limit = 3
    agent = ReActAgent(registry=registry, max_steps=max_steps_limit, llm_callback=endless_llm)
    final_state = agent.run("Endless task test")

    assert final_state.is_completed is True
    # Should execute max_steps iterations + 1 halt step
    assert len(final_state.scratchpad) == max_steps_limit + 1
    assert "Maximum step limit of 3 reached" in final_state.final_answer

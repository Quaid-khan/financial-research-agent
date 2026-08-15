"""Core ReAct (Reasoning and Acting) Agent Control Engine.

The ReAct pattern combines reasoning (Thought) and action execution (Action -> Observation)
in an iterative loop:
1. Thought: Agent analyzes current task state, memory, and previous observations to formulate next action.
2. Action: Agent chooses a registered tool and constructs input arguments (or emits final answer).
3. Observation: Agent executes chosen tool and receives returned observation data.
4. Repeat steps 1-3 until problem is solved or max_steps limit is reached.
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional, Callable
from pydantic import BaseModel, Field

from agent.config import get_settings
from agent.tools.registry import ToolRegistry, ToolResult, default_registry

# Configure logger for structured agent trajectory inspectability
logger = logging.getLogger("financial_agent")
logger.setLevel(logging.INFO)


class ToolCall(BaseModel):
    """Structured representation of a tool invocation request."""
    name: str = Field(description="Name of target tool.")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Keyword arguments passed to tool.")


class AgentStep(BaseModel):
    """Single step trajectory entry in ReAct reasoning loop."""
    step_number: int = Field(description="1-indexed step sequence count.")
    thought: str = Field(description="Agent reasoning thought before action selection.")
    action: Optional[ToolCall] = Field(default=None, description="Selected tool call request if not finished.")
    observation: Optional[str] = Field(default=None, description="Returned execution result from environment.")
    is_final: bool = Field(default=False, description="True if step emits final answer.")
    final_answer: Optional[str] = Field(default=None, description="Final answer produced by agent.")
    tokens_used: int = Field(default=0, description="Estimated tokens consumed in this step.")


class AgentState(BaseModel):
    """State object maintaining agent memory, scratchpad trace, and budget metrics."""
    task: str = Field(description="Primary user research prompt or financial query.")
    scratchpad: List[AgentStep] = Field(default_factory=list, description="Sequence of ReAct reasoning steps.")
    history: List[Dict[str, str]] = Field(default_factory=list, description="Raw conversation history trace.")
    step_count: int = Field(default=0, description="Current step index.")
    max_steps: int = Field(default=10, description="Maximum allowed reasoning steps before safety halt.")
    total_tokens: int = Field(default=0, description="Cumulative tokens consumed.")
    is_completed: bool = Field(default=False, description="True if agent reached final answer or halted.")
    final_answer: Optional[str] = Field(default=None, description="Synthesized final research answer.")

    def add_step(self, step: AgentStep) -> None:
        """Append an executed step to the scratchpad trace."""
        self.scratchpad.append(step)
        self.step_count = len(self.scratchpad)
        self.total_tokens += step.tokens_used
        if step.is_final:
            self.is_completed = True
            self.final_answer = step.final_answer

    def format_scratchpad_history(self) -> str:
        """Format scratchpad trace into text prompt for ReAct reasoning."""
        if not self.scratchpad:
            return "No previous steps taken."
            
        trace_lines = []
        for step in self.scratchpad:
            trace_lines.append(f"Step {step.step_number}:")
            trace_lines.append(f"Thought: {step.thought}")
            if step.action:
                args_json = json.dumps(step.action.arguments)
                trace_lines.append(f"Action: {step.action.name}({args_json})")
            if step.observation is not None:
                trace_lines.append(f"Observation: {step.observation}")
            if step.is_final and step.final_answer:
                trace_lines.append(f"Final Answer: {step.final_answer}")
            trace_lines.append("")
        return "\n".join(trace_lines)


class ReActAgent:
    """Autonomous Financial Agent implementing ReAct control loop."""

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        max_steps: int = 10,
        model_name: Optional[str] = None,
        llm_callback: Optional[Callable[[str, AgentState], str]] = None
    ) -> None:
        """Initialize ReAct agent.
        
        Args:
            registry: Tool registry instance (defaults to global default_registry).
            max_steps: Step limit safety cap.
            model_name: LLM model identifier override.
            llm_callback: Optional custom LLM callable (used for testing/mocking).
        """
        self.registry = registry or default_registry
        self.max_steps = max_steps
        self.llm_callback = llm_callback
        
        # Load environment configuration
        try:
            self.settings = get_settings()
            self.model_name = model_name or self.settings.gemini_model
        except Exception:
            self.settings = None
            self.model_name = model_name or "gemini-3.6-flash"

    def _call_llm(self, prompt: str, state: AgentState) -> str:
        """Generate LLM completion using configured provider or test callback."""
        if self.llm_callback:
            return self.llm_callback(prompt, state)

        if not self.settings or not self.settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is not configured in environment.")

        from google import genai
        client = genai.Client(api_key=self.settings.gemini_api_key)
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )
        return (response.text or "").strip()

    def _build_system_prompt(self, state: AgentState) -> str:
        """Construct standard ReAct system prompt explaining rules and tool format."""
        tools_text = self.registry.to_text_prompt_description()
        scratchpad_text = state.format_scratchpad_history()

        return f"""You are an Autonomous Financial Research Agent for BFSI use cases.
Solve the given financial research task using the ReAct (Reason-Act-Observe) pattern.

Available Tools:
{tools_text}

Response Format Instructions:
You MUST respond using strictly one of the two formats below:

FORMAT A (To execute a tool):
Thought: <Explain your reasoning about what information is needed next>
Action: <tool_name>({{"arg1": "value1"}})

FORMAT B (When research task is complete):
Thought: <Summarize final findings and analysis>
Final Answer: <Detailed synthesized financial research report or answer>

Current Task:
{state.task}

Scratchpad History:
{scratchpad_text}

Next Step:
"""

    def _parse_llm_response(self, response_text: str) -> tuple[str, Optional[ToolCall], bool, Optional[str]]:
        """Parse raw LLM response string into Thought, Action/ToolCall, and Final Answer.
        
        Returns:
            Tuple of (thought, tool_call, is_final, final_answer)
        """
        thought = ""
        action_name = None
        action_args = {}
        is_final = False
        final_answer = None

        # Extract Thought
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|\nFinal Answer:|$)", response_text, re.DOTALL | re.IGNORECASE)
        if thought_match:
            thought = thought_match.group(1).strip()
        else:
            thought = response_text.strip()

        # Check for Final Answer
        final_match = re.search(r"Final Answer:\s*(.*)", response_text, re.DOTALL | re.IGNORECASE)
        if final_match:
            is_final = True
            final_answer = final_match.group(1).strip()
            return thought, None, is_final, final_answer

        # Check for Action
        action_match = re.search(r"Action:\s*([a-zA-Z0-9_]+)\((.*)\)", response_text, re.DOTALL | re.IGNORECASE)
        if action_match:
            action_name = action_match.group(1).strip()
            args_str = action_match.group(2).strip()
            
            if args_str:
                try:
                    action_args = json.loads(args_str)
                except Exception:
                    # Fallback single parameter parsing if json parsing fails
                    action_args = {"query": args_str.strip('"\'')}
            
            tool_call = ToolCall(name=action_name, arguments=action_args)
            return thought, tool_call, False, None

        # Fallback if no explicit Action or Final Answer keyword was generated
        if "final answer" in response_text.lower():
            is_final = True
            final_answer = response_text
        
        return thought, None, is_final, final_answer

    def step(self, state: AgentState) -> AgentStep:
        """Execute a single ReAct iteration step."""
        step_number = state.step_count + 1
        logger.info(f"--- Agent Step {step_number}/{state.max_steps} ---")

        # 1. Thought & Action Selection via LLM
        prompt = self._build_system_prompt(state)
        raw_response = self._call_llm(prompt, state)
        
        thought, tool_call, is_final, final_answer = self._parse_llm_response(raw_response)
        logger.info(f"Thought: {thought}")

        # 2. Final Answer Handling
        if is_final:
            logger.info(f"Final Answer Reached: {final_answer}")
            return AgentStep(
                step_number=step_number,
                thought=thought,
                action=None,
                observation=None,
                is_final=True,
                final_answer=final_answer,
                tokens_used=len(prompt) // 4 + len(raw_response) // 4
            )

        # 3. Tool Execution & Observation
        observation = ""
        if tool_call:
            logger.info(f"Executing Tool: {tool_call.name} with args {tool_call.arguments}")
            tool_result: ToolResult = self.registry.execute(tool_call.name, **tool_call.arguments)
            
            if tool_result.success:
                observation = tool_result.output
            else:
                observation = f"ERROR: {tool_result.error}"
            logger.info(f"Observation: {observation}")
        else:
            observation = "ERROR: No valid Action or Final Answer detected in LLM response."

        return AgentStep(
            step_number=step_number,
            thought=thought,
            action=tool_call,
            observation=observation,
            is_final=False,
            final_answer=None,
            tokens_used=len(prompt) // 4 + len(raw_response) // 4
        )

    def run(self, task: str) -> AgentState:
        """Run complete ReAct loop until task completion or max_steps limit is reached.
        
        Args:
            task: User research prompt or financial analysis goal.
            
        Returns:
            AgentState containing final answer, scratchpad trace, and metrics.
        """
        logger.info(f"🚀 Starting Autonomous Agent Task: '{task}'")
        state = AgentState(task=task, max_steps=self.max_steps)

        while not state.is_completed:
            if state.step_count >= state.max_steps:
                logger.warning(f"⚠️ Max steps limit ({state.max_steps}) reached. Halting ReAct loop.")
                halt_step = AgentStep(
                    step_number=state.step_count + 1,
                    thought="Halt step limit reached.",
                    action=None,
                    observation=None,
                    is_final=True,
                    final_answer=f"Halted: Maximum step limit of {state.max_steps} reached without final answer.",
                    tokens_used=0
                )
                state.add_step(halt_step)
                break

            current_step = self.step(state)
            state.add_step(current_step)

        logger.info(f"🏁 Task Finished. Total Steps: {state.step_count}. Completed: {state.is_completed}")
        return state

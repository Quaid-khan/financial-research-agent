"""Tool Registry for autonomous financial research agent.

Provides registration, schema validation, serialization for function-calling APIs
(Google Gemini, Anthropic, OpenAI), and execution dispatching for agent tools.
"""

import json
from typing import Callable, Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Encapsulates the output of a tool execution."""
    tool_name: str = Field(description="Name of the executed tool.")
    success: bool = Field(description="True if execution succeeded without unhandled exceptions.")
    output: str = Field(description="String output or JSON representation of result.")
    error: Optional[str] = Field(default=None, description="Error message if execution failed.")


class ToolDefinition(BaseModel):
    """Metadata schema defining a registered agent tool."""
    name: str = Field(description="Unique tool identifier.")
    description: str = Field(description="Detailed explanation of tool utility and when the agent should invoke it.")
    parameters_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema specifying input parameter types, descriptions, and required fields."
    )
    func: Callable[..., Any] = Field(description="Executable Python callable implementing the tool logic.")

    model_config = {
        "arbitrary_types_allowed": True
    }


class ToolRegistry:
    """Registry maintaining available tools, schema formatting, and execution routing."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        func: Optional[Callable[..., Any]] = None,
        parameters_schema: Optional[Dict[str, Any]] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Register a tool with the registry directly or as a decorator."""
        schema = parameters_schema or parameters or {
            "type": "object",
            "properties": {},
            "required": []
        }

        if func is not None:
            self._tools[name] = ToolDefinition(
                name=name,
                description=description,
                parameters_schema=schema,
                func=func
            )
            return func
        else:
            def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
                self._tools[name] = ToolDefinition(
                    name=name,
                    description=description,
                    parameters_schema=schema,
                    func=fn
                )
                return fn
            return decorator

    def tool(self, name: str, description: str, parameters_schema: Optional[Dict[str, Any]] = None, parameters: Optional[Dict[str, Any]] = None) -> Callable:
        """Decorator for registering functions as agent tools."""
        return self.register(name=name, description=description, parameters_schema=parameters_schema, parameters=parameters)

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Retrieve a ToolDefinition by name."""
        return self._tools.get(name)

    def has_tool(self, name: str) -> bool:
        """Returns True if a tool is registered under the given name."""
        return name in self._tools

    def list_tools(self) -> List[ToolDefinition]:
        """Returns a list of all registered tool definitions."""
        return list(self._tools.values())

    def to_text_prompt_description(self) -> str:
        """Format all registered tools into plain text prompt descriptions for ReAct agent system prompt."""
        lines = []
        for t in self.list_tools():
            lines.append(f"- {t.name}: {t.description}")
            if t.parameters_schema and t.parameters_schema.get("properties"):
                lines.append(f"  Parameters: {json.dumps(t.parameters_schema)}")
        return "\n".join(lines)

    def execute(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None, **kwargs) -> ToolResult:
        """Dispatch execution of a registered tool with provided arguments dict or keyword arguments."""
        tool_def = self.get_tool(tool_name)
        if not tool_def:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output="",
                error=f"Tool '{tool_name}' is not registered in ToolRegistry."
            )

        combined_args = {}
        if arguments and isinstance(arguments, dict):
            combined_args.update(arguments)
        combined_args.update(kwargs)

        try:
            raw_output = tool_def.func(**combined_args)
            output_str = raw_output if isinstance(raw_output, str) else json.dumps(raw_output, indent=2)
            return ToolResult(
                tool_name=tool_name,
                success=True,
                output=output_str,
                error=None
            )
        except Exception as err:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                output="",
                error=f"Unhandled exception during tool execution: {err}"
            )


# Default global tool registry instance
default_registry = ToolRegistry()

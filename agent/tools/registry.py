"""Tool Registry for autonomous financial research agent.

Provides registration, schema validation, serialization for function-calling APIs
(Google Gemini, Anthropic, OpenAI), and execution dispatching for agent tools.
"""

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
        func: Callable[..., Any],
        parameters_schema: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a tool with the registry.
        
        Args:
            name: Unique name of the tool.
            description: Plain text explanation for the LLM.
            func: Python function to call when tool is invoked.
            parameters_schema: Optional JSON Schema dict for parameters.
        """
        if parameters_schema is None:
            parameters_schema = {
                "type": "object",
                "properties": {},
                "required": []
            }
        
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            parameters_schema=parameters_schema,
            func=func
        )

    def tool(self, name: str, description: str, parameters_schema: Optional[Dict[str, Any]] = None) -> Callable:
        """Decorator for registering functions as agent tools.
        
        Example:
            @registry.tool(name="search_filings", description="Search SEC EDGAR filings")
            def search_filings(ticker: str) -> str:
                return "..."
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.register(name=name, description=description, func=func, parameters_schema=parameters_schema)
            return func
        return decorator

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Retrieve tool definition by name."""
        return self._tools.get(name)

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def list_tools(self) -> List[ToolDefinition]:
        """List all registered tools."""
        return list(self._tools.values())

    def execute(self, name: str, **kwargs: Any) -> ToolResult:
        """Execute a registered tool by name with keyword arguments.
        
        Args:
            name: Registered tool name.
            **kwargs: Keyword arguments passed to tool function.
            
        Returns:
            ToolResult containing execution outcome and output/error string.
        """
        tool_def = self.get_tool(name)
        if not tool_def:
            return ToolResult(
                tool_name=name,
                success=False,
                output="",
                error=f"Tool '{name}' is not registered in ToolRegistry."
            )

        try:
            result = tool_def.func(**kwargs)
            output_str = str(result) if not isinstance(result, str) else result
            return ToolResult(
                tool_name=name,
                success=True,
                output=output_str,
                error=None
            )
        except Exception as err:
            return ToolResult(
                tool_name=name,
                success=False,
                output="",
                error=f"Tool execution exception in '{name}': {err}"
            )

    def to_gemini_declarations(self) -> List[Dict[str, Any]]:
        """Export tools formatted for Google Gemini function_declarations API.
        
        Returns:
            List of function declaration dicts compatible with Google Gemini Client.
        """
        declarations = []
        for t in self.list_tools():
            declarations.append({
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters_schema
            })
        return declarations

    def to_text_prompt_description(self) -> str:
        """Export tools as human-readable text for prompt-based ReAct agent loop.
        
        Returns:
            Formatted string describing each available tool and its arguments.
        """
        lines = []
        for t in self.list_tools():
            props = t.parameters_schema.get("properties", {})
            args_str = ", ".join([f"{k}: {v.get('type', 'any')}" for k, v in props.items()])
            lines.append(f"- {t.name}({args_str}): {t.description}")
        return "\n".join(lines)


# Global default tool registry instance
default_registry = ToolRegistry()

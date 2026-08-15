"""Financial research tools subpackage.

==============================================================================
GEMINI FUNCTION-CALLING COMPATIBILITY SPECIFICATION
==============================================================================
This agent architecture targets Google's Gemini SDK (`google-genai` / `google-generativeai`).

Key Design & Implementation Conventions for Tools:
1. Tool Schemas: All tools defined in `agent/tools/` must export Pydantic models
   or Python functions that map cleanly to Gemini FunctionDeclarations.
2. Function Declaration Objects: When passing tools to Gemini client model calls:
   `tools = [function_schema]` or `types.Tool(function_declarations=[...])`.
3. Parameter Types: Use explicit Pydantic schema types (STRING, INTEGER, NUMBER, BOOLEAN, OBJECT, ARRAY).
4. ReAct Tool Loop: The agent orchestration loop parses Gemini's `function_call`
   response structure (`response.candidates[0].content.parts[].function_call`)
   and returns `function_response` parts back to the chat session.
==============================================================================
"""

__all__ = []

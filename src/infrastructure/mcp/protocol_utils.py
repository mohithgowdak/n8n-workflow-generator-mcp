"""MCP protocol utilities."""

import json
from typing import Any, Dict, Optional, List
from mcp.types import Tool, TextContent
from .error_handler import MCPErrorHandler, MCPErrorCode
from .response_formatter import MCPResponseFormatter, MCPContentType
from ...infrastructure.logger.logger import Logger


class MCPProtocolUtils:
    """Utilities for MCP protocol operations."""
    
    @staticmethod
    def create_tool_from_definition(tool_def: Dict[str, Any]) -> Tool:
        """Create an MCP Tool from a tool definition."""
        return Tool(
            name=tool_def["name"],
            description=tool_def["description"],
            inputSchema=tool_def.get("inputSchema", {})
        )
    
    @staticmethod
    def create_text_content(
        text: str,
        content_type: MCPContentType = MCPContentType.TEXT
    ) -> List[TextContent]:
        """Create TextContent for MCP response."""
        return [TextContent(type="text", text=text)]
    
    @staticmethod
    def create_success_content(
        data: Any,
        message: Optional[str] = None,
        content_type: MCPContentType = MCPContentType.JSON
    ) -> List[TextContent]:
        """Create success content for MCP response."""
        formatted = MCPResponseFormatter.format_success(
            data=data,
            content_type=content_type,
            message=message
        )
        return [TextContent(type="text", text=formatted)]
    
    @staticmethod
    def create_error_content(
        error: Exception,
        tool_name: Optional[str] = None
    ) -> List[TextContent]:
        """Create error content for MCP response."""
        error_info = MCPErrorHandler.handle_error(error, tool_name)
        formatted = MCPResponseFormatter.format_error(
            error_code=error_info["code"],
            error_message=error_info["message"],
            details=error_info.get("data")
        )
        return [TextContent(type="text", text=formatted)]
    
    @staticmethod
    def validate_tool_arguments(
        arguments: Dict[str, Any],
        schema: Dict[str, Any],
        tool_name: str
    ) -> Dict[str, Any]:
        """Validate tool arguments against schema."""
        logger = Logger.get_instance()
        
        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in arguments:
                raise ValueError(
                    f"Missing required argument '{field}' for tool '{tool_name}'"
                )
        
        # Validate types (basic validation)
        properties = schema.get("properties", {})
        for field, value in arguments.items():
            if field in properties:
                prop_schema = properties[field]
                expected_type = prop_schema.get("type")
                
                if expected_type == "string" and not isinstance(value, str):
                    raise ValueError(
                        f"Argument '{field}' must be a string for tool '{tool_name}'"
                    )
                elif expected_type == "integer" and not isinstance(value, int):
                    raise ValueError(
                        f"Argument '{field}' must be an integer for tool '{tool_name}'"
                    )
                elif expected_type == "boolean" and not isinstance(value, bool):
                    raise ValueError(
                        f"Argument '{field}' must be a boolean for tool '{tool_name}'"
                    )
                elif expected_type == "object" and not isinstance(value, dict):
                    raise ValueError(
                        f"Argument '{field}' must be an object for tool '{tool_name}'"
                    )
                elif expected_type == "array" and not isinstance(value, list):
                    raise ValueError(
                        f"Argument '{field}' must be an array for tool '{tool_name}'"
                    )
        
        logger.debug(f"Validated arguments for tool '{tool_name}': {arguments}")
        return arguments
    
    @staticmethod
    def format_tool_result(
        result: Any,
        as_json: bool = True
    ) -> str:
        """Format tool result for MCP response."""
        if as_json:
            if isinstance(result, str):
                # Try to parse as JSON, if fails return as-is
                try:
                    json.loads(result)
                    return result
                except (json.JSONDecodeError, ValueError):
                    # Return as JSON string
                    return MCPResponseFormatter.format_json({"result": result})
            else:
                return MCPResponseFormatter.format_json(result)
        else:
            return str(result)


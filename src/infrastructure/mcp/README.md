# MCP Protocol Implementation

This module contains the MCP (Model Context Protocol) implementation utilities for the n8n Workflow Generator MCP server.

## Components

### 1. Error Handler (`error_handler.py`)

Handles MCP protocol errors and maps domain errors to MCP error codes.

**Features:**
- Maps domain errors to MCP error codes
- Provides standardized error responses
- Logs errors with context
- Supports custom error details

**Usage:**
```python
from .error_handler import MCPErrorHandler, MCPErrorCode

# Handle an error
error_info = MCPErrorHandler.handle_error(error, tool_name="my_tool")

# Create custom error response
error_response = MCPErrorHandler.create_mcp_error_response(
    code=MCPErrorCode.VALIDATION_ERROR,
    message="Invalid input",
    details={"field": "prompt"}
)
```

### 2. Response Formatter (`response_formatter.py`)

Formats responses in various content types for MCP protocol.

**Features:**
- Multiple content types: JSON, Markdown, HTML, Text
- Success response formatting
- Error response formatting
- Table formatting
- Dictionary/list conversion

**Usage:**
```python
from .response_formatter import MCPResponseFormatter, MCPContentType

# Format success response
formatted = MCPResponseFormatter.format_success(
    data={"result": "success"},
    message="Operation completed",
    content_type=MCPContentType.JSON
)

# Format error response
formatted = MCPResponseFormatter.format_error(
    error_code="MCP-001",
    error_message="Invalid request",
    details={"field": "prompt"}
)
```

### 3. Protocol Utils (`protocol_utils.py`)

Utilities for MCP protocol operations.

**Features:**
- Tool creation from definitions
- Content creation for responses
- Argument validation
- Result formatting
- Error content creation

**Usage:**
```python
from .protocol_utils import MCPProtocolUtils

# Create tool from definition
tool = MCPProtocolUtils.create_tool_from_definition(tool_def)

# Validate arguments
validated = MCPProtocolUtils.validate_tool_arguments(
    arguments=args,
    schema=tool_schema,
    tool_name="my_tool"
)

# Create success content
content = MCPProtocolUtils.create_success_content(
    data={"result": "success"},
    message="Done"
)

# Create error content
content = MCPProtocolUtils.create_error_content(error, tool_name="my_tool")
```

## Error Codes

The following MCP error codes are defined:

- `MCP-001`: Invalid Request
- `MCP-002`: Invalid Params
- `MCP-003`: Method Not Found
- `MCP-004`: Internal Error
- `MCP-005`: Resource Not Found
- `MCP-006`: Unauthorized
- `MCP-007`: Rate Limited
- `MCP-008`: Validation Error
- `MCP-009`: Configuration Error
- `MCP-010`: Integration Error

## Integration

The MCP utilities are integrated into the main server (`src/__main__.py`):

1. **Tool Registration**: Uses `MCPProtocolUtils.create_tool_from_definition()` to create MCP tools
2. **Argument Validation**: Uses `MCPProtocolUtils.validate_tool_arguments()` before tool execution
3. **Error Handling**: Uses `MCPProtocolUtils.create_error_content()` for error responses
4. **Response Formatting**: Uses `MCPProtocolUtils.create_success_content()` for success responses

## Example Flow

```python
# 1. Tool is called
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    # 2. Get tool from registry
    tool = tool_registry.get_tool(name)
    
    # 3. Validate arguments
    validated = MCPProtocolUtils.validate_tool_arguments(
        arguments, tool.schema, name
    )
    
    # 4. Execute tool
    try:
        result = await tool.handler(validated)
        # 5. Format success response
        return MCPProtocolUtils.create_success_content(result)
    except Exception as error:
        # 6. Format error response
        return MCPProtocolUtils.create_error_content(error, name)
```

## Testing

To test the MCP implementation:

```python
from src.infrastructure.mcp import (
    MCPErrorHandler,
    MCPErrorCode,
    MCPResponseFormatter,
    MCPContentType,
    MCPProtocolUtils
)

# Test error handling
error_info = MCPErrorHandler.handle_error(ValueError("Test error"))
assert error_info["code"] == MCPErrorCode.INVALID_PARAMS.value

# Test response formatting
formatted = MCPResponseFormatter.format_success({"test": "data"})
assert "test" in formatted

# Test protocol utils
content = MCPProtocolUtils.create_success_content({"result": "ok"})
assert len(content) == 1
```


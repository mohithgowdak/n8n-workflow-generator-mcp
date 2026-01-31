"""MCP error handling utilities."""

from typing import Optional, Dict, Any
from enum import Enum
from ...domain.errors import (
    DomainError,
    ValidationError,
    ResourceNotFoundError,
    UnauthorizedError,
    RateLimitError,
    ConfigurationError,
    IntegrationError,
    N8nAPIError
)
from ...infrastructure.logger.logger import Logger


class MCPErrorCode(str, Enum):
    """MCP error codes."""
    INVALID_REQUEST = "MCP-001"
    INVALID_PARAMS = "MCP-002"
    METHOD_NOT_FOUND = "MCP-003"
    INTERNAL_ERROR = "MCP-004"
    RESOURCE_NOT_FOUND = "MCP-005"
    UNAUTHORIZED = "MCP-006"
    RATE_LIMITED = "MCP-007"
    VALIDATION_ERROR = "MCP-008"
    CONFIGURATION_ERROR = "MCP-009"
    INTEGRATION_ERROR = "MCP-010"


class MCPErrorHandler:
    """Handler for MCP protocol errors."""
    
    @staticmethod
    def handle_error(error: Exception, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """Handle an error and convert it to MCP error format."""
        logger = Logger.get_instance()
        
        # Log the error
        context = f" in tool '{tool_name}'" if tool_name else ""
        logger.error(f"Error{context}: {error}")
        
        # Map domain errors to MCP error codes
        error_code = MCPErrorHandler._map_error_to_code(error)
        error_message = str(error)
        
        # Add additional context for certain error types
        if isinstance(error, ValidationError):
            error_message = f"Validation failed: {error_message}"
        elif isinstance(error, ResourceNotFoundError):
            error_message = f"Resource not found: {error_message}"
        elif isinstance(error, UnauthorizedError):
            error_message = f"Unauthorized: {error_message}"
        elif isinstance(error, RateLimitError):
            error_message = f"Rate limit exceeded: {error_message}"
        elif isinstance(error, ConfigurationError):
            error_message = f"Configuration error: {error_message}"
        elif isinstance(error, IntegrationError):
            error_message = f"Integration error: {error_message}"
        elif isinstance(error, N8nAPIError):
            error_message = f"n8n API error: {error_message}"
        
        return {
            "code": error_code.value,
            "message": error_message,
            "data": {
                "error_type": type(error).__name__,
                "tool": tool_name
            }
        }
    
    @staticmethod
    def _map_error_to_code(error: Exception) -> MCPErrorCode:
        """Map a domain error to MCP error code."""
        if isinstance(error, ValidationError):
            return MCPErrorCode.VALIDATION_ERROR
        elif isinstance(error, ResourceNotFoundError):
            return MCPErrorCode.RESOURCE_NOT_FOUND
        elif isinstance(error, UnauthorizedError):
            return MCPErrorCode.UNAUTHORIZED
        elif isinstance(error, RateLimitError):
            return MCPErrorCode.RATE_LIMITED
        elif isinstance(error, ConfigurationError):
            return MCPErrorCode.CONFIGURATION_ERROR
        elif isinstance(error, IntegrationError):
            return MCPErrorCode.INTEGRATION_ERROR
        elif isinstance(error, N8nAPIError):
            return MCPErrorCode.INTEGRATION_ERROR
        elif isinstance(error, ValueError):
            return MCPErrorCode.INVALID_PARAMS
        elif isinstance(error, KeyError):
            return MCPErrorCode.INVALID_PARAMS
        else:
            return MCPErrorCode.INTERNAL_ERROR
    
    @staticmethod
    def create_mcp_error_response(
        code: MCPErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a standardized MCP error response."""
        response = {
            "code": code.value,
            "message": message
        }
        
        if details:
            response["data"] = details
        
        return response


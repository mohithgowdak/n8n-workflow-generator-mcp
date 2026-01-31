"""Domain error types."""


class DomainError(Exception):
    """Base domain error."""
    pass


class ValidationError(DomainError):
    """Validation failures."""
    pass


class ResourceNotFoundError(DomainError):
    """Resource not found."""
    pass


class UnauthorizedError(DomainError):
    """Unauthorized access."""
    pass


class RateLimitError(DomainError):
    """Rate limit exceeded."""
    pass


class ConfigurationError(DomainError):
    """Configuration issues."""
    pass


class IntegrationError(DomainError):
    """Integration failures."""
    pass


class N8nAPIError(DomainError):
    """n8n API errors."""
    pass


class LLMError(DomainError):
    """LLM service errors."""
    pass


class MCPProtocolError(DomainError):
    """MCP protocol errors."""
    pass



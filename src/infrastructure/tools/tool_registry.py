"""Tool registry for managing MCP tools."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class ToolDefinition:
    """Definition of an MCP tool."""
    name: str
    description: str
    handler: Any  # Async function
    schema: Dict[str, Any]  # JSON schema for input


class ToolRegistry:
    """Central registry of all available tools."""
    
    _instance: Optional["ToolRegistry"] = None
    _tools: Dict[str, ToolDefinition]
    
    def __new__(cls):
        """Create singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def register_tool(self, tool: ToolDefinition) -> None:
        """Register a new tool."""
        if tool.name in self._tools:
            import sys
            sys.stderr.write(f"Tool '{tool.name}' is already registered and will be overwritten.\n")
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_all_tools(self) -> List[ToolDefinition]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def get_tools_for_mcp(self) -> List[Dict[str, Any]]:
        """Convert tools to MCP format for list_tools response."""
        tools_list = []
        for tool in self.get_all_tools():
            tools_list.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.schema,
            })
        return tools_list


#!/usr/bin/env python3
"""List all available MCP tools."""

import sys
import json
sys.path.insert(0, 'src')

from src.infrastructure.tools.tool_registry import ToolRegistry
from src.infrastructure.tools.workflow_tools import register_workflow_tools

# Initialize registry and register tools
registry = ToolRegistry.get_instance()
register_workflow_tools(None, registry)

# Get all tools
tools = registry.get_all_tools()

print("=" * 70)
print("Available MCP Tools")
print("=" * 70)
print()

for i, tool in enumerate(tools, 1):
    print(f"{i}. {tool.name}")
    print(f"   Description: {tool.description}")
    print()
    
    # Show parameters
    schema = tool.schema
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    if properties:
        print("   Parameters:")
        for param_name, param_def in properties.items():
            param_type = param_def.get("type", "unknown")
            param_desc = param_def.get("description", "")
            is_required = param_name in required
            req_marker = " (required)" if is_required else " (optional)"
            print(f"     - {param_name}: {param_type}{req_marker}")
            if param_desc:
                print(f"       {param_desc}")
        print()
    
    print("-" * 70)
    print()

print(f"Total: {len(tools)} tools registered")


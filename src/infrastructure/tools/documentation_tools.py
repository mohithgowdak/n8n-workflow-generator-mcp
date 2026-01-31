"""MCP tools for tool documentation."""

import json
from typing import Dict, Any
from .tool_registry import ToolDefinition, ToolRegistry
from ..logger.logger import Logger


def register_documentation_tools(registry: ToolRegistry):
    """Register documentation tools."""
    
    logger = Logger.get_instance()
    
    # Tools documentation
    async def tools_documentation_handler(arguments: Dict[str, Any]) -> str:
        """Get documentation for MCP tools."""
        topic = arguments.get('topic', '')
        depth = arguments.get('depth', 'essentials')
        
        # Get all registered tools
        all_tools = registry.get_all_tools()
        
        if not topic or topic == 'overview':
            # Return overview of all tools
            tools_overview = {
                'version': '0.1.0',
                'total_tools': len(all_tools),
                'tools': []
            }
            
            for tool in all_tools:
                tools_overview['tools'].append({
                    'name': tool.name,
                    'description': tool.description[:200] + '...' if len(tool.description) > 200 else tool.description
                })
            
            if depth == 'full':
                tools_overview['detailed_tools'] = [
                    {
                        'name': tool.name,
                        'description': tool.description,
                        'schema': tool.schema
                    }
                    for tool in all_tools
                ]
            
            return json.dumps(tools_overview)
        
        # Find specific tool
        tool = registry.get_tool(topic)
        if not tool:
            return json.dumps({
                'error': f'Tool "{topic}" not found',
                'available_tools': [t.name for t in all_tools]
            })
        
        # Return tool documentation
        doc = {
            'name': tool.name,
            'description': tool.description,
            'schema': tool.schema
        }
        
        if depth == 'full':
            # Add usage examples and more details
            doc['usage'] = {
                'example': f"Call {tool.name} with parameters matching the schema",
                'schema_description': 'See schema property for parameter details'
            }
        
        return json.dumps(doc)
    
    tools_documentation_tool = ToolDefinition(
        name="tools_documentation",
        description="Get documentation for n8n MCP tools. Call without parameters for quick start guide. Use topic parameter to get documentation for specific tools. Use depth='full' for comprehensive documentation.",
        handler=tools_documentation_handler,
        schema={
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Tool name (e.g., 'search_nodes') or 'overview' for general guide. Leave empty for quick reference."
                },
                "depth": {
                    "type": "string",
                    "enum": ["essentials", "full"],
                    "default": "essentials",
                    "description": "Level of detail. 'essentials' (default) for quick reference, 'full' for comprehensive docs."
                }
            }
        }
    )
    
    # Register tool
    registry.register_tool(tools_documentation_tool)
    
    logger.info(f"Registered {1} documentation tool")


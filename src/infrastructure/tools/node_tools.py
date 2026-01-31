"""MCP tools for node discovery and information."""

import json
from typing import Dict, Any, Optional
from .tool_registry import ToolDefinition, ToolRegistry
from ..database.node_repository import NodeRepository
from ..logger.logger import Logger
from pathlib import Path


def register_node_tools(
    node_repository: Optional[NodeRepository],
    registry: ToolRegistry
):
    """Register all node-related tools."""
    
    logger = Logger.get_instance()
    
    # Search nodes tool
    async def search_nodes_handler(arguments: Dict[str, Any]) -> str:
        """Search n8n nodes by keyword."""
        if not node_repository:
            return json.dumps({
                'error': 'Node database not configured. Please set N8N_NODE_DB_PATH environment variable.',
                'results': []
            })
        
        query = arguments.get('query', '')
        if not query:
            return json.dumps({
                'error': 'Query is required',
                'results': []
            })
        
        try:
            limit = arguments.get('limit', 20)
            mode = arguments.get('mode', 'OR')
            source = arguments.get('source', 'all')
            include_examples = arguments.get('includeExamples', False)
            
            results = node_repository.search_nodes(
                query=query,
                limit=limit,
                mode=mode,
                source=source,
                include_examples=include_examples
            )
            
            return json.dumps({
                'results': results,
                'count': len(results)
            })
        except Exception as e:
            logger.error(f"Error searching nodes: {e}")
            return json.dumps({
                'error': str(e),
                'results': []
            })
    
    search_nodes_tool = ToolDefinition(
        name="search_nodes",
        description="Search n8n nodes by keyword with optional real-world examples. Returns max 20 results by default. Use includeExamples=true to get top 2 template configs per node.",
        handler=search_nodes_handler,
        schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search terms. Use quotes for exact phrase."
                },
                "limit": {
                    "type": "number",
                    "description": "Max results (default 20)",
                    "default": 20
                },
                "mode": {
                    "type": "string",
                    "enum": ["OR", "AND", "FUZZY"],
                    "description": "OR=any word, AND=all words, FUZZY=typo-tolerant",
                    "default": "OR"
                },
                "includeExamples": {
                    "type": "boolean",
                    "description": "Include top 2 real-world configuration examples from popular templates (default: false)",
                    "default": False
                },
                "source": {
                    "type": "string",
                    "enum": ["all", "core", "community", "verified"],
                    "description": "Filter by node source: all=everything (default), core=n8n base nodes, community=community nodes, verified=verified community nodes only",
                    "default": "all"
                }
            },
            "required": ["query"]
        }
    )
    
    # Get node tool
    async def get_node_handler(arguments: Dict[str, Any]) -> str:
        """Get node information by node type."""
        if not node_repository:
            return json.dumps({
                'error': 'Node database not configured. Please set N8N_NODE_DB_PATH environment variable.',
                'node': None
            })
        
        node_type = arguments.get('nodeType', '')
        if not node_type:
            return json.dumps({
                'error': 'nodeType is required',
                'node': None
            })
        
        try:
            detail = arguments.get('detail', 'standard')
            mode = arguments.get('mode', 'info')
            
            node = node_repository.get_node(
                node_type=node_type,
                detail=detail,
                mode=mode
            )
            
            if not node:
                return json.dumps({
                    'error': f'Node not found: {node_type}',
                    'node': None
                })
            
            return json.dumps({
                'node': node
            })
        except Exception as e:
            logger.error(f"Error getting node: {e}")
            return json.dumps({
                'error': str(e),
                'node': None
            })
    
    get_node_tool = ToolDefinition(
        name="get_node",
        description="Get node info with progressive detail levels and multiple modes. Detail: minimal (~200 tokens), standard (~1-2K, default), full (~3-8K). Modes: info (default), docs (markdown documentation), search_properties (find properties), versions/compare/breaking/migrations (version info).",
        handler=get_node_handler,
        schema={
            "type": "object",
            "properties": {
                "nodeType": {
                    "type": "string",
                    "description": "Full node type: 'nodes-base.httpRequest' or 'nodes-langchain.agent'"
                },
                "detail": {
                    "type": "string",
                    "enum": ["minimal", "standard", "full"],
                    "default": "standard",
                    "description": "Information detail level. standard=essential properties (recommended), full=everything"
                },
                "mode": {
                    "type": "string",
                    "enum": ["info", "docs", "search_properties", "versions", "compare", "breaking", "migrations"],
                    "default": "info",
                    "description": "Operation mode. info=node schema, docs=readable markdown documentation, search_properties=find specific properties, versions/compare/breaking/migrations=version info"
                },
                "includeTypeInfo": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include type structure metadata (type category, JS type, validation rules). Only applies to mode=info."
                },
                "propertyQuery": {
                    "type": "string",
                    "description": "Search query for properties (required when mode=search_properties)"
                }
            },
            "required": ["nodeType"]
        }
    )
    
    # Register tools
    registry.register_tool(search_nodes_tool)
    registry.register_tool(get_node_tool)
    
    logger.info(f"Registered {2} node discovery tools")


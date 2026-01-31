"""MCP tools for n8n API management."""

import json
from typing import Dict, Any, Optional
from .tool_registry import ToolDefinition, ToolRegistry
from ..n8n.repositories.n8n_workflow_repository import N8nWorkflowRepository
from ..logger.logger import Logger


def register_n8n_api_tools(
    workflow_repository: Optional[N8nWorkflowRepository],
    registry: ToolRegistry
):
    """Register all n8n API management tools."""
    
    logger = Logger.get_instance()
    
    if not workflow_repository:
        logger.info("n8n API not configured. n8n API tools disabled.")
        return
    
    # Get workflow tool
    async def get_workflow_handler(arguments: Dict[str, Any]) -> str:
        """Get workflow by ID with different detail levels."""
        workflow_id = arguments.get('id', '')
        if not workflow_id:
            return json.dumps({
                'error': 'Workflow ID is required',
                'workflow': None
            })
        
        try:
            mode = arguments.get('mode', 'full')
            workflow = await workflow_repository.get_by_id(workflow_id)
            
            # Filter based on mode
            if mode == 'minimal':
                result = {
                    'id': workflow.get('id'),
                    'name': workflow.get('name'),
                    'active': workflow.get('active', False),
                    'tags': workflow.get('tags', [])
                }
            elif mode == 'structure':
                result = {
                    'id': workflow.get('id'),
                    'name': workflow.get('name'),
                    'nodes': workflow.get('nodes', []),
                    'connections': workflow.get('connections', {})
                }
            elif mode == 'details':
                # Full workflow + execution stats if available
                result = workflow.copy()
                # Could add execution stats here if API supports it
            else:  # full
                result = workflow
            
            return json.dumps({
                'workflow': result,
                'mode': mode
            })
        except Exception as e:
            logger.error(f"Error getting workflow: {e}")
            return json.dumps({
                'error': str(e),
                'workflow': None
            })
    
    get_workflow_tool = ToolDefinition(
        name="n8n_get_workflow",
        description="Get workflow by ID with different detail levels. Use mode='full' for complete workflow, 'details' for metadata+stats, 'structure' for nodes/connections only, 'minimal' for id/name/active/tags.",
        handler=get_workflow_handler,
        schema={
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Workflow ID"
                },
                "mode": {
                    "type": "string",
                    "enum": ["full", "details", "structure", "minimal"],
                    "default": "full",
                    "description": "Detail level: full=complete workflow, details=full+execution stats, structure=nodes/connections topology, minimal=metadata only"
                }
            },
            "required": ["id"]
        }
    )
    
    # List workflows tool
    async def list_workflows_handler(arguments: Dict[str, Any]) -> str:
        """List workflows with optional filters."""
        try:
            limit = arguments.get('limit')
            cursor = arguments.get('cursor')
            
            result = await workflow_repository.list(limit=limit, cursor=cursor)
            
            return json.dumps({
                'workflows': result.get('data', result) if isinstance(result, dict) else result,
                'nextCursor': result.get('nextCursor') if isinstance(result, dict) else None,
                'count': len(result.get('data', result) if isinstance(result, dict) else result)
            })
        except Exception as e:
            logger.error(f"Error listing workflows: {e}")
            return json.dumps({
                'error': str(e),
                'workflows': []
            })
    
    list_workflows_tool = ToolDefinition(
        name="n8n_list_workflows",
        description="List workflows with optional pagination. Returns array of workflows with metadata.",
        handler=list_workflows_handler,
        schema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "number",
                    "description": "Maximum number of workflows to return"
                },
                "cursor": {
                    "type": "string",
                    "description": "Pagination cursor for next page"
                }
            }
        }
    )
    
    # Update full workflow tool
    async def update_full_workflow_handler(arguments: Dict[str, Any]) -> str:
        """Update workflow with full replacement."""
        workflow_id = arguments.get('id', '')
        if not workflow_id:
            return json.dumps({
                'error': 'Workflow ID is required',
                'workflow': None
            })
        
        try:
            # Build workflow object from arguments
            workflow = {}
            if 'name' in arguments:
                workflow['name'] = arguments['name']
            if 'nodes' in arguments:
                workflow['nodes'] = arguments['nodes']
            if 'connections' in arguments:
                workflow['connections'] = arguments['connections']
            if 'settings' in arguments:
                workflow['settings'] = arguments['settings']
            
            # Get existing workflow and merge
            existing = await workflow_repository.get_by_id(workflow_id)
            workflow = {**existing, **workflow}
            
            updated = await workflow_repository.update(workflow_id, workflow)
            
            return json.dumps({
                'workflow': updated,
                'message': 'Workflow updated successfully'
            })
        except Exception as e:
            logger.error(f"Error updating workflow: {e}")
            return json.dumps({
                'error': str(e),
                'workflow': None
            })
    
    update_full_workflow_tool = ToolDefinition(
        name="n8n_update_full_workflow",
        description="Full workflow update. Requires complete nodes[] and connections{}. For incremental updates, modify the workflow object and call this tool.",
        handler=update_full_workflow_handler,
        schema={
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Workflow ID to update"
                },
                "name": {
                    "type": "string",
                    "description": "New workflow name"
                },
                "nodes": {
                    "type": "array",
                    "description": "Complete array of workflow nodes",
                    "items": {"type": "object"}
                },
                "connections": {
                    "type": "object",
                    "description": "Complete connections object"
                },
                "settings": {
                    "type": "object",
                    "description": "Workflow settings to update"
                }
            },
            "required": ["id"]
        }
    )
    
    # Delete workflow tool
    async def delete_workflow_handler(arguments: Dict[str, Any]) -> str:
        """Delete a workflow."""
        workflow_id = arguments.get('id', '')
        if not workflow_id:
            return json.dumps({
                'error': 'Workflow ID is required'
            })
        
        try:
            await workflow_repository.delete(workflow_id)
            return json.dumps({
                'message': f'Workflow {workflow_id} deleted successfully'
            })
        except Exception as e:
            logger.error(f"Error deleting workflow: {e}")
            return json.dumps({
                'error': str(e)
            })
    
    delete_workflow_tool = ToolDefinition(
        name="n8n_delete_workflow",
        description="Delete a workflow by ID. This action cannot be undone.",
        handler=delete_workflow_handler,
        schema={
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Workflow ID to delete"
                }
            },
            "required": ["id"]
        }
    )
    
    # Health check tool
    async def health_check_handler(arguments: Dict[str, Any]) -> str:
        """Check n8n API connectivity and health."""
        try:
            health = await workflow_repository.api_client.health_check()
            return json.dumps({
                'status': 'ok',
                'health': health
            })
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return json.dumps({
                'status': 'error',
                'error': str(e)
            })
    
    health_check_tool = ToolDefinition(
        name="n8n_health_check",
        description="Check n8n API connectivity and health status.",
        handler=health_check_handler,
        schema={
            "type": "object",
            "properties": {}
        }
    )
    
    # Register all tools
    registry.register_tool(get_workflow_tool)
    registry.register_tool(list_workflows_tool)
    registry.register_tool(update_full_workflow_tool)
    registry.register_tool(delete_workflow_tool)
    registry.register_tool(health_check_tool)
    
    logger.info(f"Registered {5} n8n API management tools")


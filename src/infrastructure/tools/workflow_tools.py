"""MCP tools for workflow generation."""

import json
from typing import Dict, Any, Optional
from .tool_registry import ToolDefinition, ToolRegistry
from ...services.workflow_generation_service import WorkflowGenerationService
from ...infrastructure.logger.logger import Logger
from ...infrastructure.n8n.util.n8n_docs_fetcher import N8nDocsFetcher
from ...env import config


def register_workflow_tools(
    service: Optional[WorkflowGenerationService],
    registry: ToolRegistry
):
    """Register all workflow-related tools."""
    
    logger = Logger.get_instance()
    
    # Generate workflow tool
    async def generate_workflow_handler(arguments: Dict[str, Any]) -> str:
        """Generate a workflow from a prompt."""
        prompt = arguments.get('prompt', '')
        workflow_name = arguments.get('workflow_name')
        
        if not prompt:
            return json.dumps({
                'error': 'Prompt is required',
                'workflow': None
            })
        
        try:
            # Fetch n8n API documentation for LLM context
            api_docs = None
            docs_url = None
            if config.n8n_api_url:
                try:
                    docs_fetcher = N8nDocsFetcher(config.n8n_api_url)
                    api_docs = await docs_fetcher.fetch_docs()
                    docs_url = docs_fetcher.get_docs_url()
                    if api_docs:
                        logger.info(f"Fetched n8n API docs from {docs_url}")
                    else:
                        logger.warning(f"Could not fetch n8n API docs from {docs_url}")
                except Exception as e:
                    logger.warning(f"Error fetching n8n API docs: {e}")
            
            # Note: In a real implementation, this would call Cursor's LLM
            # For now, we return a structured response that includes:
            # 1. The user's prompt
            # 2. The n8n API documentation (if available)
            # 3. Instructions for the LLM to generate the workflow
            
            # Build context for LLM
            context = {
                'user_prompt': prompt,
                'workflow_name': workflow_name or 'Generated Workflow',
                'n8n_api_docs_available': api_docs is not None,
                'n8n_api_docs_url': docs_url,
            }
            
            # Include API docs in response if available
            if api_docs:
                context['n8n_api_docs'] = api_docs[:5000]  # Limit to first 5000 chars to avoid huge responses
                context['n8n_api_docs_note'] = 'Full documentation available at: ' + (docs_url or '')
            
            return json.dumps({
                'error': None,
                'context': context,
                'workflow': {
                    'name': workflow_name or 'Generated Workflow',
                    'nodes': [],
                    'connections': {},
                    'settings': {
                        'executionOrder': 'v1'
                    }
                },
                'instructions': {
                    'message': 'Use the provided n8n API documentation to generate a valid n8n workflow JSON structure.',
                    'requirements': [
                        'Generate nodes based on the n8n API documentation',
                        'Ensure all node types are valid according to the API docs',
                        'Include proper node connections',
                        'Set appropriate node positions',
                        'Include required parameters for each node type'
                    ],
                    'api_docs_reference': docs_url or 'http://localhost:5678/api/v1/docs/'
                },
                'note': 'This response includes n8n API documentation context. Cursor\'s LLM should use this to generate a proper workflow.'
            })
        except Exception as e:
            logger.error(f"Error generating workflow: {e}")
            return json.dumps({
                'error': str(e),
                'workflow': None
            })
    
    # Build description with API docs reference
    api_docs_note = ""
    if config.n8n_api_url:
        docs_url = f"{config.n8n_api_url.rstrip('/')}/api/v1/docs"
        api_docs_note = f" The tool automatically fetches n8n API documentation from {docs_url} to ensure generated workflows use valid node types and parameters."
    
    generate_workflow_tool = ToolDefinition(
        name="generate_workflow",
        description=f"Generate an n8n workflow from a natural language prompt. The workflow will be validated and can be deployed to an n8n instance.{api_docs_note} The tool includes n8n API documentation in the response context to guide workflow generation.",
        handler=generate_workflow_handler,
        schema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Natural language description of the workflow to generate (e.g., 'Create a workflow that fetches data from an API and saves it to a database'). The tool will automatically include n8n API documentation to ensure valid node types and parameters are used."
                },
                "workflow_name": {
                    "type": "string",
                    "description": "Optional name for the generated workflow"
                }
            },
            "required": ["prompt"]
        }
    )
    
    # Validate workflow tool
    async def validate_workflow_handler(arguments: Dict[str, Any]) -> str:
        """Validate a workflow structure."""
        workflow_json = arguments.get('workflow')
        
        if not workflow_json:
            return json.dumps({
                'valid': False,
                'errors': ['Workflow is required'],
                'warnings': []
            })
        
        try:
            if isinstance(workflow_json, str):
                workflow = json.loads(workflow_json)
            else:
                workflow = workflow_json
            
            if service:
                result = await service.validate_workflow(workflow)
            else:
                # Fallback validation if service not available
                from ...infrastructure.n8n.util.n8n_validator import validate_workflow_structure
                errors = validate_workflow_structure(workflow)
                result = {'valid': len(errors) == 0, 'errors': errors, 'warnings': []}
            
            return json.dumps(result)
        except json.JSONDecodeError as e:
            return json.dumps({
                'valid': False,
                'errors': [f'Invalid JSON: {str(e)}'],
                'warnings': []
            })
        except Exception as e:
            logger.error(f"Error validating workflow: {e}")
            return json.dumps({
                'valid': False,
                'errors': [str(e)],
                'warnings': []
            })
    
    validate_workflow_tool = ToolDefinition(
        name="validate_workflow",
        description="Validate an n8n workflow structure. Returns validation errors and warnings.",
        handler=validate_workflow_handler,
        schema={
            "type": "object",
            "properties": {
                "workflow": {
                    "type": "object",
                    "description": "The workflow JSON object to validate"
                }
            },
            "required": ["workflow"]
        }
    )
    
    # Deploy workflow tool
    async def deploy_workflow_handler(arguments: Dict[str, Any]) -> str:
        """Deploy a workflow to n8n instance."""
        if not service:
            return json.dumps({
                'error': 'n8n API not configured. Please set N8N_API_URL and N8N_API_KEY environment variables.',
                'workflow': None
            })
        
        workflow_json = arguments.get('workflow')
        activate = arguments.get('activate', False)
        
        if not workflow_json:
            return json.dumps({
                'error': 'Workflow is required',
                'workflow': None
            })
        
        try:
            if isinstance(workflow_json, str):
                workflow = json.loads(workflow_json)
            else:
                workflow = workflow_json
            
            deployed = await service.deploy_workflow(workflow, activate=activate)
            return json.dumps({
                'error': None,
                'workflow': deployed,
                'message': 'Workflow deployed successfully'
            })
        except Exception as e:
            logger.error(f"Error deploying workflow: {e}")
            return json.dumps({
                'error': str(e),
                'workflow': None
            })
    
    deploy_workflow_tool = ToolDefinition(
        name="deploy_workflow",
        description="Deploy a workflow to the configured n8n instance. Optionally activate it.",
        handler=deploy_workflow_handler,
        schema={
            "type": "object",
            "properties": {
                "workflow": {
                    "type": "object",
                    "description": "The workflow JSON object to deploy"
                },
                "activate": {
                    "type": "boolean",
                    "description": "Whether to activate the workflow after deployment",
                    "default": False
                }
            },
            "required": ["workflow"]
        }
    )
    
    # Register all tools
    registry.register_tool(generate_workflow_tool)
    registry.register_tool(validate_workflow_tool)
    registry.register_tool(deploy_workflow_tool)


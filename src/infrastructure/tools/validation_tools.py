"""MCP tools for node and workflow validation."""

import json
from typing import Dict, Any, Optional
from .tool_registry import ToolDefinition, ToolRegistry
from ..database.node_repository import NodeRepository
from ..logger.logger import Logger


def register_validation_tools(
    node_repository: Optional[NodeRepository],
    registry: ToolRegistry
):
    """Register validation tools."""
    
    logger = Logger.get_instance()
    
    # Validate node tool
    async def validate_node_handler(arguments: Dict[str, Any]) -> str:
        """Validate node configuration."""
        if not node_repository:
            return json.dumps({
                'error': 'Node database not configured',
                'valid': False,
                'errors': []
            })
        
        node_type = arguments.get('nodeType', '')
        config = arguments.get('config', {})
        mode = arguments.get('mode', 'full')
        
        if not node_type:
            return json.dumps({
                'error': 'nodeType is required',
                'valid': False,
                'errors': []
            })
        
        try:
            # Get node information
            node = node_repository.get_node(node_type, detail='full')
            if not node:
                return json.dumps({
                    'nodeType': node_type,
                    'valid': False,
                    'errors': [{
                        'type': 'invalid_configuration',
                        'property': '',
                        'message': f'Node type not found: {node_type}'
                    }],
                    'warnings': [],
                    'suggestions': []
                })
            
            # Basic validation based on mode
            errors = []
            warnings = []
            suggestions = []
            
            if mode == 'minimal':
                # Quick check for required fields
                properties = node.get('properties', [])
                if isinstance(properties, list):
                    for prop in properties:
                        if prop.get('required') and prop.get('name') not in config:
                            errors.append({
                                'type': 'missing_required_field',
                                'property': prop.get('name', ''),
                                'message': f"Required field '{prop.get('name')}' is missing"
                            })
            else:  # full mode
                # More comprehensive validation
                properties = node.get('properties', [])
                if isinstance(properties, list):
                    for prop in properties:
                        prop_name = prop.get('name', '')
                        
                        # Check required fields
                        if prop.get('required') and prop_name not in config:
                            errors.append({
                                'type': 'missing_required_field',
                                'property': prop_name,
                                'message': f"Required field '{prop_name}' is missing"
                            })
                        
                        # Check if value is provided but might be invalid
                        if prop_name in config:
                            value = config[prop_name]
                            prop_type = prop.get('type', '')
                            
                            # Basic type checking
                            if prop_type == 'number' and not isinstance(value, (int, float)):
                                warnings.append({
                                    'type': 'type_mismatch',
                                    'property': prop_name,
                                    'message': f"Expected number, got {type(value).__name__}"
                                })
                            elif prop_type == 'boolean' and not isinstance(value, bool):
                                warnings.append({
                                    'type': 'type_mismatch',
                                    'property': prop_name,
                                    'message': f"Expected boolean, got {type(value).__name__}"
                                })
                            elif prop_type == 'string' and not isinstance(value, str):
                                warnings.append({
                                    'type': 'type_mismatch',
                                    'property': prop_name,
                                    'message': f"Expected string, got {type(value).__name__}"
                                })
            
            # Build result
            result = {
                'nodeType': node_type,
                'workflowNodeType': node_type,
                'displayName': node.get('displayName', node_type),
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings,
                'suggestions': suggestions,
                'summary': {
                    'hasErrors': len(errors) > 0,
                    'errorCount': len(errors),
                    'warningCount': len(warnings),
                    'suggestionCount': len(suggestions)
                }
            }
            
            if mode == 'minimal':
                result['missingRequiredFields'] = [
                    e['property'] for e in errors if e['type'] == 'missing_required_field'
                ]
            
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Error validating node: {e}")
            return json.dumps({
                'nodeType': node_type,
                'valid': False,
                'errors': [{
                    'type': 'validation_error',
                    'property': '',
                    'message': str(e)
                }],
                'warnings': [],
                'suggestions': []
            })
    
    validate_node_tool = ToolDefinition(
        name="validate_node",
        description="Validate node configuration. Use mode='minimal' for quick required fields check, mode='full' for comprehensive validation with errors, warnings, and suggestions.",
        handler=validate_node_handler,
        schema={
            "type": "object",
            "properties": {
                "nodeType": {
                    "type": "string",
                    "description": "Node type with prefix: 'nodes-base.slack'"
                },
                "config": {
                    "type": "object",
                    "description": "Configuration object to validate. Use {} for empty config"
                },
                "mode": {
                    "type": "string",
                    "enum": ["minimal", "full"],
                    "default": "full",
                    "description": "Validation mode: 'full' (default) for comprehensive validation, 'minimal' for quick required fields check"
                },
                "profile": {
                    "type": "string",
                    "enum": ["minimal", "runtime", "ai-friendly", "strict"],
                    "default": "runtime",
                    "description": "Validation profile for mode=full: 'minimal', 'runtime' (default), 'ai-friendly', 'strict'"
                }
            },
            "required": ["nodeType", "config"]
        }
    )
    
    # Register tool
    registry.register_tool(validate_node_tool)
    
    logger.info(f"Registered {1} validation tool")


"""n8n workflow validation utilities."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ValidationError
from ...logger.logger import Logger


class WorkflowNode(BaseModel):
    """Workflow node schema."""
    id: str
    name: str
    type: str
    typeVersion: float
    position: tuple[float, float]
    parameters: Dict[str, Any]
    credentials: Optional[Dict[str, Any]] = None
    disabled: Optional[bool] = None
    notes: Optional[str] = None
    notesInFlow: Optional[bool] = None
    continueOnFail: Optional[bool] = None
    retryOnFail: Optional[bool] = None
    maxTries: Optional[int] = None
    waitBetweenTries: Optional[int] = None
    alwaysOutputData: Optional[bool] = None
    executeOnce: Optional[bool] = None


def is_trigger_node(node_type: str) -> bool:
    """Check if node is a trigger node."""
    trigger_types = [
        'webhook', 'webhookTrigger', 'schedule', 'manualTrigger',
        'executeWorkflowTrigger', 'chatTrigger', 'mcpTrigger'
    ]
    return any(trigger in node_type.lower() for trigger in trigger_types)


def is_non_executable_node(node_type: str) -> bool:
    """Check if node is non-executable (e.g., sticky note)."""
    return 'stickyNote' in node_type.lower() or 'note' in node_type.lower()


def clean_workflow_for_create(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """Clean workflow data for creation."""
    cleaned = workflow.copy()
    
    # Remove read-only fields
    for field in ['id', 'createdAt', 'updatedAt', 'versionId', 'meta', 'active', 'tags']:
        cleaned.pop(field, None)
    
    # Ensure settings with defaults
    if not cleaned.get('settings') or len(cleaned.get('settings', {})) == 0:
        cleaned['settings'] = {
            'executionOrder': 'v1',
            'saveDataErrorExecution': 'all',
            'saveDataSuccessExecution': 'all',
            'saveManualExecutions': True,
            'saveExecutionProgress': True,
        }
    
    return cleaned


def clean_workflow_for_update(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """Clean workflow data for update."""
    cleaned = workflow.copy()
    
    # Remove read-only/computed fields
    read_only_fields = [
        'id', 'createdAt', 'updatedAt', 'versionId', 'versionCounter',
        'meta', 'staticData', 'pinData', 'tags', 'description',
        'isArchived', 'usedCredentials', 'sharedWithProjects',
        'triggerCount', 'shared', 'active', 'activeVersionId', 'activeVersion'
    ]
    for field in read_only_fields:
        cleaned.pop(field, None)
    
    # Filter settings to known properties
    if cleaned.get('settings') and isinstance(cleaned['settings'], dict):
        known_settings = {
            'saveExecutionProgress', 'saveManualExecutions',
            'saveDataErrorExecution', 'saveDataSuccessExecution',
            'executionTimeout', 'errorWorkflow', 'timezone',
            'executionOrder', 'callerPolicy', 'callerIds',
            'timeSavedPerExecution', 'availableInMCP'
        }
        filtered_settings = {
            k: v for k, v in cleaned['settings'].items()
            if k in known_settings
        }
        if filtered_settings:
            cleaned['settings'] = filtered_settings
        else:
            cleaned['settings'] = {'executionOrder': 'v1'}
    else:
        cleaned['settings'] = {'executionOrder': 'v1'}
    
    return cleaned


def validate_workflow_structure(workflow: Dict[str, Any]) -> List[str]:
    """Validate workflow structure and return list of errors."""
    errors: List[str] = []
    
    # Check required fields
    if not workflow.get('name'):
        errors.append('Workflow name is required')
    
    nodes = workflow.get('nodes', [])
    if not nodes or len(nodes) == 0:
        errors.append('Workflow must have at least one node')
    
    # Check for executable nodes
    if nodes:
        has_executable = any(not is_non_executable_node(node.get('type', '')) for node in nodes)
        if not has_executable:
            errors.append('Workflow must have at least one executable node. Sticky notes alone cannot form a valid workflow.')
    
    if not workflow.get('connections'):
        errors.append('Workflow connections are required')
    
    # Check minimum viable workflow
    if len(nodes) == 1:
        single_node = nodes[0]
        node_type = single_node.get('type', '')
        is_webhook = 'webhook' in node_type.lower()
        if not is_webhook:
            errors.append(
                f'Single non-webhook node workflow is invalid. Current node: "{single_node.get("name")}" ({node_type}). '
                'Add another node to process the data.'
            )
    
    # Check for disconnected nodes
    if len(nodes) > 1 and workflow.get('connections'):
        executable_nodes = [n for n in nodes if not is_non_executable_node(n.get('type', ''))]
        connections = workflow.get('connections', {})
        connection_count = len(connections)
        
        if connection_count == 0 and len(executable_nodes) > 1:
            node_names = [n.get('name') for n in executable_nodes[:2]]
            errors.append(
                f'Multi-node workflow has no connections between nodes. '
                f'Add a connection from "{node_names[0]}" to "{node_names[1]}".'
            )
        elif connection_count > 0 or len(executable_nodes) > 1:
            connected_nodes = set()
            all_connection_types = ['main', 'error', 'ai_tool', 'ai_languageModel', 'ai_memory', 'ai_embedding', 'ai_vectorStore']
            
            for source_name, conn_data in connections.items():
                connected_nodes.add(source_name)
                if isinstance(conn_data, dict):
                    for conn_type in all_connection_types:
                        conn_array = conn_data.get(conn_type)
                        if isinstance(conn_array, list):
                            for outputs in conn_array:
                                if isinstance(outputs, list):
                                    for target in outputs:
                                        if isinstance(target, dict) and target.get('node'):
                                            connected_nodes.add(target['node'])
            
            disconnected = [
                n for n in executable_nodes
                if n.get('name') not in connected_nodes
                and not is_trigger_node(n.get('type', ''))
            ]
            
            if disconnected:
                disconnected_list = ', '.join(f'"{n.get("name")}" ({n.get("type")})' for n in disconnected)
                errors.append(f'Disconnected nodes detected: {disconnected_list}. Each node must have at least one connection.')
    
    # Validate nodes
    for i, node in enumerate(nodes):
        try:
            WorkflowNode(**node)
            
            # Check node type format
            node_type = node.get('type', '')
            if node_type.startswith('nodes-base.'):
                errors.append(
                    f'Invalid node type "{node_type}" at index {i}. '
                    f'Use "n8n-nodes-base.{node_type[11:]}" instead.'
                )
            elif '.' not in node_type:
                errors.append(
                    f'Invalid node type "{node_type}" at index {i}. '
                    'Node types must include package prefix (e.g., "n8n-nodes-base.webhook").'
                )
        except ValidationError as e:
            errors.append(f'Invalid node at index {i}: {", ".join(str(err) for err in e.errors())}')
        except Exception as e:
            errors.append(f'Invalid node at index {i}: {str(e)}')
    
    # Validate active workflows have triggers
    if workflow.get('active') is True and nodes:
        activatable_triggers = [
            n for n in nodes
            if not n.get('disabled') and is_trigger_node(n.get('type', ''))
        ]
        if not activatable_triggers:
            errors.append(
                'Cannot activate workflow: No activatable trigger nodes found. '
                'Workflows must have at least one enabled trigger node.'
            )
    
    return errors


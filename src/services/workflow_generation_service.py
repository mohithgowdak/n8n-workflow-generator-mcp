"""Workflow generation service using Cursor's built-in LLM."""

import json
from typing import Dict, Any, Optional
from ..domain.types import Workflow
from ..infrastructure.n8n.repositories.n8n_workflow_repository import N8nWorkflowRepository
from ..infrastructure.n8n.util.n8n_validator import validate_workflow_structure
from ..infrastructure.logger.logger import Logger


class WorkflowGenerationService:
    """Service for generating n8n workflows from prompts."""
    
    def __init__(self, workflow_repository: N8nWorkflowRepository):
        """Initialize workflow generation service."""
        self.workflow_repository = workflow_repository
        self.logger = Logger.get_instance()
    
    async def generate_workflow(
        self,
        prompt: str,
        workflow_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a workflow from a prompt.
        
        Note: This service relies on Cursor's built-in LLM to generate workflows.
        The actual LLM call happens through the MCP tool handler, which has access
        to Cursor's LLM context.
        """
        # This is a placeholder - actual generation happens in the MCP tool handler
        # which has access to Cursor's LLM
        raise NotImplementedError(
            "Workflow generation should be called through MCP tools, "
            "which have access to Cursor's LLM context."
        )
    
    async def validate_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a workflow structure."""
        errors = validate_workflow_structure(workflow)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': []  # Could add warnings in the future
        }
    
    async def deploy_workflow(
        self,
        workflow: Dict[str, Any],
        activate: bool = False
    ) -> Dict[str, Any]:
        """Deploy a workflow to n8n instance."""
        # Validate first
        validation_result = await self.validate_workflow(workflow)
        if not validation_result['valid']:
            from ..domain.errors import ValidationError
            raise ValidationError(
                f"Workflow validation failed: {'; '.join(validation_result['errors'])}"
            )
        
        # Create workflow
        created = await self.workflow_repository.create(workflow)
        
        # Activate if requested
        if activate:
            workflow_id = created.get('id')
            if workflow_id:
                await self.workflow_repository.activate(workflow_id)
                created['active'] = True
        
        return created
    
    async def update_workflow(
        self,
        workflow_id: str,
        workflow: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update an existing workflow."""
        # Validate first
        validation_result = await self.validate_workflow(workflow)
        if not validation_result['valid']:
            from ..domain.errors import ValidationError
            raise ValidationError(
                f"Workflow validation failed: {'; '.join(validation_result['errors'])}"
            )
        
        return await self.workflow_repository.update(workflow_id, workflow)


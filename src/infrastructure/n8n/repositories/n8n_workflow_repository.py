"""n8n workflow repository."""

from typing import Dict, Any, List, Optional
from .base_repository import BaseN8nRepository
from ..util.n8n_validator import validate_workflow_structure, clean_workflow_for_create, clean_workflow_for_update
from ...logger.logger import Logger
# Use absolute import to avoid relative import resolution issues in test environment
try:
    from src.domain.errors import ValidationError, ResourceNotFoundError
except ImportError:
    # Fallback for when running as package
    from ...domain.errors import ValidationError, ResourceNotFoundError


class N8nWorkflowRepository(BaseN8nRepository):
    """Repository for n8n workflow operations."""
    
    async def create(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow."""
        # Validate structure
        errors = validate_workflow_structure(workflow)
        if errors:
            raise ValidationError(f"Workflow validation failed: {'; '.join(errors)}")
        
        # Clean workflow
        cleaned = clean_workflow_for_create(workflow)
        
        # Create via API
        try:
            return await self.api_client.create_workflow(cleaned)
        except Exception as e:
            self._logger.error(f"Failed to create workflow: {e}")
            raise
    
    async def get_by_id(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow by ID."""
        try:
            return await self.api_client.get_workflow(workflow_id)
        except Exception as e:
            if '404' in str(e) or 'not found' in str(e).lower():
                raise ResourceNotFoundError(f"Workflow {workflow_id} not found")
            self._logger.error(f"Failed to get workflow: {e}")
            raise
    
    async def update(self, workflow_id: str, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Update a workflow."""
        # Validate structure
        errors = validate_workflow_structure(workflow)
        if errors:
            raise ValidationError(f"Workflow validation failed: {'; '.join(errors)}")
        
        # Clean workflow
        cleaned = clean_workflow_for_update(workflow)
        
        # Update via API
        try:
            return await self.api_client.update_workflow(workflow_id, cleaned)
        except Exception as e:
            self._logger.error(f"Failed to update workflow: {e}")
            raise
    
    async def delete(self, workflow_id: str) -> Dict[str, Any]:
        """Delete a workflow."""
        try:
            return await self.api_client.delete_workflow(workflow_id)
        except Exception as e:
            self._logger.error(f"Failed to delete workflow: {e}")
            raise
    
    async def list(self, limit: Optional[int] = None, cursor: Optional[str] = None) -> Dict[str, Any]:
        """List workflows."""
        try:
            return await self.api_client.list_workflows(limit=limit, cursor=cursor)
        except Exception as e:
            self._logger.error(f"Failed to list workflows: {e}")
            raise
    
    async def activate(self, workflow_id: str) -> Dict[str, Any]:
        """Activate a workflow."""
        try:
            return await self.api_client.activate_workflow(workflow_id)
        except Exception as e:
            self._logger.error(f"Failed to activate workflow: {e}")
            raise
    
    async def deactivate(self, workflow_id: str) -> Dict[str, Any]:
        """Deactivate a workflow."""
        try:
            return await self.api_client.deactivate_workflow(workflow_id)
        except Exception as e:
            self._logger.error(f"Failed to deactivate workflow: {e}")
            raise


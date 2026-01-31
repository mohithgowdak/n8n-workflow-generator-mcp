"""n8n API client for interacting with n8n instances."""

import asyncio
from typing import Optional, Dict, Any, List
import httpx
from ...logger.logger import Logger


class N8nApiError(Exception):
    """n8n API error."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class N8nApiClient:
    """Client for n8n API operations."""
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 30000,
        max_retries: int = 3
    ):
        """Initialize n8n API client."""
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout / 1000  # Convert to seconds
        self.max_retries = max_retries
        self.logger = Logger.get_instance()
        
        # Ensure baseUrl ends with /api/v1
        if not self.base_url.endswith('/api/v1'):
            self.api_url = f"{self.base_url}/api/v1"
        else:
            self.api_url = self.base_url
        
        # Create HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.api_url,
            timeout=self.timeout,
            headers={
                'X-N8N-API-KEY': api_key,
                'Content-Type': 'application/json',
            }
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check n8n API health."""
        try:
            # Try healthz endpoint
            healthz_url = self.base_url + '/healthz'
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(healthz_url)
                if response.status_code == 200 and response.json().get('status') == 'ok':
                    return {
                        'status': 'ok',
                        'n8nVersion': None,  # Would need version endpoint
                        'features': {}
                    }
            
            # Fallback: try listing workflows
            await self.list_workflows(limit=1)
            return {
                'status': 'ok',
                'n8nVersion': None,
                'features': {}
            }
        except Exception as e:
            raise N8nApiError(f"Health check failed: {e}")
    
    async def create_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow."""
        try:
            response = await self.client.post('/workflows', json=workflow)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise N8nApiError(
                f"Failed to create workflow: {e.response.text}",
                status_code=e.response.status_code,
                response=e.response.json() if e.response.headers.get('content-type', '').startswith('application/json') else None
            )
        except Exception as e:
            raise N8nApiError(f"Failed to create workflow: {e}")
    
    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get a workflow by ID."""
        try:
            response = await self.client.get(f'/workflows/{workflow_id}')
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise N8nApiError(
                f"Failed to get workflow: {e.response.text}",
                status_code=e.response.status_code
            )
        except Exception as e:
            raise N8nApiError(f"Failed to get workflow: {e}")
    
    async def update_workflow(self, workflow_id: str, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Update a workflow."""
        try:
            # Try PUT first (newer n8n)
            try:
                response = await self.client.put(f'/workflows/{workflow_id}', json=workflow)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 405:  # Method Not Allowed
                    # Fallback to PATCH
                    response = await self.client.patch(f'/workflows/{workflow_id}', json=workflow)
                    response.raise_for_status()
                    return response.json()
                raise
        except httpx.HTTPStatusError as e:
            raise N8nApiError(
                f"Failed to update workflow: {e.response.text}",
                status_code=e.response.status_code
            )
        except Exception as e:
            raise N8nApiError(f"Failed to update workflow: {e}")
    
    async def delete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Delete a workflow."""
        try:
            response = await self.client.delete(f'/workflows/{workflow_id}')
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise N8nApiError(
                f"Failed to delete workflow: {e.response.text}",
                status_code=e.response.status_code
            )
        except Exception as e:
            raise N8nApiError(f"Failed to delete workflow: {e}")
    
    async def list_workflows(
        self,
        limit: Optional[int] = None,
        cursor: Optional[str] = None
    ) -> Dict[str, Any]:
        """List workflows."""
        try:
            params = {}
            if limit:
                params['limit'] = limit
            if cursor:
                params['cursor'] = cursor
            
            response = await self.client.get('/workflows', params=params)
            response.raise_for_status()
            data = response.json()
            
            # Handle both modern and legacy response formats
            if isinstance(data, list):
                return {'data': data, 'nextCursor': None}
            return data
        except httpx.HTTPStatusError as e:
            raise N8nApiError(
                f"Failed to list workflows: {e.response.text}",
                status_code=e.response.status_code
            )
        except Exception as e:
            raise N8nApiError(f"Failed to list workflows: {e}")
    
    async def activate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Activate a workflow."""
        try:
            response = await self.client.post(f'/workflows/{workflow_id}/activate')
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise N8nApiError(
                f"Failed to activate workflow: {e.response.text}",
                status_code=e.response.status_code
            )
        except Exception as e:
            raise N8nApiError(f"Failed to activate workflow: {e}")
    
    async def deactivate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Deactivate a workflow."""
        try:
            response = await self.client.post(f'/workflows/{workflow_id}/deactivate')
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise N8nApiError(
                f"Failed to deactivate workflow: {e.response.text}",
                status_code=e.response.status_code
            )
        except Exception as e:
            raise N8nApiError(f"Failed to deactivate workflow: {e}")


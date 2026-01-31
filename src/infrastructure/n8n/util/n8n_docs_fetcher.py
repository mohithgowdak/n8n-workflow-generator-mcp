"""Utility to fetch n8n API documentation."""

import json
import httpx
from typing import Optional, Dict, Any
from ...logger.logger import Logger


class N8nDocsFetcher:
    """Fetches and formats n8n API documentation for LLM context."""
    
    def __init__(self, base_url: str, timeout: int = 10):
        """Initialize docs fetcher."""
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.logger = Logger.get_instance()
        self._cached_docs: Optional[str] = None
    
    async def fetch_docs(self, use_cache: bool = True) -> Optional[str]:
        """
        Fetch n8n API documentation from /api/v1/docs endpoint.
        
        Returns formatted documentation string or None if unavailable.
        """
        # Return cached docs if available
        if use_cache and self._cached_docs:
            return self._cached_docs
        
        docs_url = f"{self.base_url}/api/v1/docs"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(docs_url)
                response.raise_for_status()
                
                # Try to parse as JSON (OpenAPI/Swagger format)
                try:
                    docs_json = response.json()
                    formatted_docs = self._format_openapi_docs(docs_json)
                    self._cached_docs = formatted_docs
                    return formatted_docs
                except Exception:
                    # If not JSON, return as text
                    self._cached_docs = response.text
                    return self._cached_docs
                    
        except httpx.TimeoutException:
            self.logger.warning(f"Timeout fetching n8n docs from {docs_url}")
            return None
        except httpx.HTTPStatusError as e:
            self.logger.warning(f"Failed to fetch n8n docs: {e.response.status_code}")
            return None
        except Exception as e:
            self.logger.warning(f"Error fetching n8n docs: {e}")
            return None
    
    def _format_openapi_docs(self, docs_json: Dict[str, Any]) -> str:
        """Format OpenAPI/Swagger documentation for LLM context."""
        lines = []
        
        # Add API info
        info = docs_json.get('info', {})
        if info:
            lines.append(f"# n8n API Documentation")
            lines.append(f"")
            lines.append(f"**Version**: {info.get('version', 'Unknown')}")
            lines.append(f"**Title**: {info.get('title', 'n8n API')}")
            if info.get('description'):
                lines.append(f"**Description**: {info.get('description')}")
            lines.append(f"")
        
        # Add servers
        servers = docs_json.get('servers', [])
        if servers:
            lines.append("## API Endpoints")
            for server in servers:
                lines.append(f"- {server.get('url', '')} - {server.get('description', '')}")
            lines.append("")
        
        # Add paths (API endpoints)
        paths = docs_json.get('paths', {})
        if paths:
            lines.append("## Available API Endpoints")
            lines.append("")
            
            for path, methods in paths.items():
                lines.append(f"### {path}")
                lines.append("")
                
                for method, details in methods.items():
                    if method.upper() in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
                        summary = details.get('summary', '')
                        description = details.get('description', '')
                        parameters = details.get('parameters', [])
                        request_body = details.get('requestBody', {})
                        responses = details.get('responses', {})
                        
                        lines.append(f"**{method.upper()}** {path}")
                        if summary:
                            lines.append(f"- Summary: {summary}")
                        if description:
                            lines.append(f"- Description: {description}")
                        
                        if parameters:
                            lines.append("- Parameters:")
                            for param in parameters:
                                param_name = param.get('name', '')
                                param_type = param.get('schema', {}).get('type', '')
                                param_desc = param.get('description', '')
                                required = param.get('required', False)
                                req_marker = " (required)" if required else ""
                                lines.append(f"  - `{param_name}` ({param_type}){req_marker}: {param_desc}")
                        
                        if request_body:
                            content = request_body.get('content', {})
                            if content:
                                lines.append("- Request Body:")
                                for content_type, schema in content.items():
                                    lines.append(f"  - Content-Type: {content_type}")
                                    schema_ref = schema.get('schema', {})
                                    if schema_ref:
                                        lines.append(f"    Schema: {json.dumps(schema_ref, indent=4)}")
                        
                        if responses:
                            lines.append("- Responses:")
                            for status_code, response_info in responses.items():
                                desc = response_info.get('description', '')
                                lines.append(f"  - {status_code}: {desc}")
                        
                        lines.append("")
        
        # Add components/schemas
        components = docs_json.get('components', {})
        schemas = components.get('schemas', {}) if components else {}
        if schemas:
            lines.append("## Data Schemas")
            lines.append("")
            for schema_name, schema_def in schemas.items():
                lines.append(f"### {schema_name}")
                properties = schema_def.get('properties', {})
                if properties:
                    lines.append("Properties:")
                    for prop_name, prop_def in properties.items():
                        prop_type = prop_def.get('type', '')
                        prop_desc = prop_def.get('description', '')
                        required = prop_name in schema_def.get('required', [])
                        req_marker = " (required)" if required else ""
                        lines.append(f"  - `{prop_name}` ({prop_type}){req_marker}: {prop_desc}")
                lines.append("")
        
        return "\n".join(lines)
    
    def clear_cache(self):
        """Clear cached documentation."""
        self._cached_docs = None
    
    def get_docs_url(self) -> str:
        """Get the documentation URL."""
        return f"{self.base_url}/api/v1/docs"


#!/usr/bin/env python3
"""Main entry point for n8n Workflow Generator MCP server."""

import sys
import os
import asyncio
from pathlib import Path
from typing import Optional

# Ensure the project root is in the Python path
# This handles cases where the working directory isn't set correctly
_project_root = Path(__file__).parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Change to project root directory if not already there
# This ensures relative imports work correctly
if os.getcwd() != str(_project_root):
    os.chdir(_project_root)

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
except ImportError:
    print(
        "Error: MCP SDK not installed. Please install it with: pip install mcp",
        file=sys.stderr
    )
    sys.exit(1)

from .env import config
from .infrastructure.logger.logger import Logger
from .infrastructure.n8n.util.n8n_api_client import N8nApiClient
from .infrastructure.n8n.repositories.n8n_workflow_repository import N8nWorkflowRepository
from .services.workflow_generation_service import WorkflowGenerationService
from .infrastructure.tools.tool_registry import ToolRegistry
from .infrastructure.tools.workflow_tools import register_workflow_tools
from .infrastructure.mcp import MCPProtocolUtils, MCPErrorHandler


class N8nWorkflowGeneratorServer:
    """n8n Workflow Generator MCP Server."""
    
    def __init__(self):
        """Initialize the server."""
        self.logger = Logger.get_instance()
        
        # Initialize MCP server
        self.server = Server(
            name="n8n-workflow-generator",
            version="0.1.0"
        )
        
        # Initialize n8n API client if configured
        self.api_client = None
        self.service = None
        self.tool_registry = ToolRegistry.get_instance()
        
        if config.n8n_api_url and config.n8n_api_key:
            try:
                self.api_client = N8nApiClient(
                    base_url=config.n8n_api_url,
                    api_key=config.n8n_api_key
                )
                workflow_repository = N8nWorkflowRepository(self.api_client)
                self.service = WorkflowGenerationService(workflow_repository)
                
                # Register tools
                register_workflow_tools(self.service, self.tool_registry)
            except Exception as e:
                self.logger.warning(f"Failed to initialize n8n client: {e}. Deployment features disabled.")
        else:
            self.logger.info("n8n API not configured. Only workflow generation and validation available.")
            # Register tools with None service (validation-only mode)
            register_workflow_tools(None, self.tool_registry)
        
        # Setup handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP handlers."""
        # Setup list_tools handler
        @self.server.list_tools()
        async def list_tools() -> list:
            """List all available tools."""
            try:
                from mcp.types import Tool
                tools = self.tool_registry.get_tools_for_mcp()
                return [MCPProtocolUtils.create_tool_from_definition(tool) for tool in tools]
            except Exception as e:
                self.logger.error(f"Error in list_tools handler: {e}")
                raise
        
        # Setup call_tool handler
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list:
            """Call a tool by name."""
            try:
                tool = self.tool_registry.get_tool(name)
                if not tool:
                    raise ValueError(f"Tool '{name}' not found")
                
                # Validate arguments
                try:
                    validated_args = MCPProtocolUtils.validate_tool_arguments(
                        arguments=arguments,
                        schema=tool.schema,
                        tool_name=name
                    )
                except ValueError as validation_error:
                    self.logger.error(f"Tool validation error: {validation_error}")
                    return MCPProtocolUtils.create_error_content(
                        validation_error,
                        tool_name=name
                    )
                
                # Execute tool handler
                result = await tool.handler(validated_args)
                
                # Tool handlers return JSON strings, wrap in TextContent
                return MCPProtocolUtils.create_text_content(result)
                
            except Exception as error:
                self.logger.error(f"Tool execution error: {error}")
                return MCPProtocolUtils.create_error_content(error, tool_name=name)
    
    async def run(self):
        """Run the MCP server."""
        try:
            if config.n8n_api_url:
                self.logger.info(f"n8n API configured: {config.n8n_api_url}")
            else:
                self.logger.info("n8n API not configured (deployment features disabled)")
            
            self.logger.info(f"Registered {len(self.tool_registry.get_all_tools())} tools")
            print("n8n Workflow Generator MCP server running on stdio", file=sys.stderr)
            
            # Run the server with stdio transport
            async with stdio_server() as (read_stream, write_stream):
                initialization_options = self.server.create_initialization_options()
                await self.server.run(
                    read_stream,
                    write_stream,
                    initialization_options
                )
        except Exception as error:
            self.logger.error(f"Failed to start server: {error}")
            raise
        finally:
            # Cleanup
            if self.api_client:
                await self.api_client.close()


def main():
    """Main entry point."""
    try:
        server = N8nWorkflowGeneratorServer()
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\nShutting down...", file=sys.stderr)
        sys.exit(0)
    except Exception as error:
        print(f"Error initializing server: {error}", file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()



#!/usr/bin/env python3
"""Quick check for errors and logical issues."""

import sys
import traceback

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def check_imports():
    """Check all critical imports."""
    errors = []
    
    try:
        from src.env import config
        print("[OK] Config import")
    except Exception as e:
        errors.append(f"Config import: {e}")
    
    try:
        from src.infrastructure.logger.logger import Logger
        print("[OK] Logger import")
    except Exception as e:
        errors.append(f"Logger import: {e}")
    
    try:
        from src.infrastructure.tools.tool_registry import ToolRegistry
        print("[OK] ToolRegistry import")
    except Exception as e:
        errors.append(f"ToolRegistry import: {e}")
    
    try:
        from src.infrastructure.tools.workflow_tools import register_workflow_tools
        print("[OK] Workflow tools import")
    except Exception as e:
        errors.append(f"Workflow tools import: {e}")
    
    try:
        from src.infrastructure.mcp import MCPProtocolUtils, MCPErrorHandler
        print("[OK] MCP utilities import")
    except Exception as e:
        errors.append(f"MCP utilities import: {e}")
    
    try:
        from src.infrastructure.n8n.util.n8n_validator import validate_workflow_structure
        print("[OK] n8n validator import")
    except Exception as e:
        errors.append(f"n8n validator import: {e}")
    
    try:
        from src.services.workflow_generation_service import WorkflowGenerationService
        print("[OK] Workflow service import")
    except Exception as e:
        errors.append(f"Workflow service import: {e}")
    
    return errors

def check_logical_issues():
    """Check for logical issues."""
    issues = []
    
    # Check tool registry
    try:
        from src.infrastructure.tools.tool_registry import ToolRegistry
        registry = ToolRegistry.get_instance()
        
        # Check if tools can be registered
        from src.infrastructure.tools.workflow_tools import register_workflow_tools
        register_workflow_tools(None, registry)
        
        tools = registry.get_all_tools()
        if len(tools) != 3:
            issues.append(f"Expected 3 tools, got {len(tools)}")
        else:
            print(f"[OK] {len(tools)} tools registered")
        
        # Check tool format
        mcp_tools = registry.get_tools_for_mcp()
        for tool in mcp_tools:
            if "name" not in tool or "description" not in tool or "inputSchema" not in tool:
                issues.append(f"Tool {tool.get('name', 'unknown')} missing required fields")
        
        if not issues:
            print("[OK] Tool registry format correct")
            
    except Exception as e:
        issues.append(f"Tool registry check: {e}")
    
    # Check MCP protocol utils
    try:
        from src.infrastructure.mcp.protocol_utils import MCPProtocolUtils
        
        # Test tool creation
        test_tool = {
            "name": "test_tool",
            "description": "Test",
            "inputSchema": {"type": "object", "properties": {}}
        }
        mcp_tool = MCPProtocolUtils.create_tool_from_definition(test_tool)
        if mcp_tool.name != "test_tool":
            issues.append("Tool creation failed")
        else:
            print("[OK] MCP tool creation works")
            
    except Exception as e:
        issues.append(f"MCP protocol utils check: {e}")
    
    return issues

def main():
    """Run all checks."""
    print("Checking for errors and logical issues...\n")
    
    # Check imports
    print("=== Import Checks ===")
    import_errors = check_imports()
    
    # Check logical issues
    print("\n=== Logical Checks ===")
    logical_issues = check_logical_issues()
    
    # Summary
    print("\n=== Summary ===")
    all_issues = import_errors + logical_issues
    
    if all_issues:
        print(f"[ERROR] Found {len(all_issues)} issue(s):")
        for issue in all_issues:
            print(f"  - {issue}")
        return 1
    else:
        print("[SUCCESS] No errors or logical issues found!")
        print("\nThe server is ready to run.")
        return 0

if __name__ == "__main__":
    sys.exit(main())


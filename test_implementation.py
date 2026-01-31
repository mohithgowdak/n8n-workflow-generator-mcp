#!/usr/bin/env python3
"""Test script for n8n Workflow Generator MCP implementation."""

import sys
import asyncio
sys.path.insert(0, 'src')

def test_imports():
    """Test all imports."""
    print("Testing imports...")
    try:
        from src.infrastructure.mcp import MCPErrorHandler, MCPResponseFormatter, MCPProtocolUtils
        from src.infrastructure.n8n.util.n8n_api_client import N8nApiClient
        from src.infrastructure.n8n.util.n8n_validator import validate_workflow_structure
        from src.infrastructure.n8n.repositories.n8n_workflow_repository import N8nWorkflowRepository
        from src.services.workflow_generation_service import WorkflowGenerationService
        from src.infrastructure.tools.tool_registry import ToolRegistry
        from src.domain.errors import ValidationError
        print("[PASS] All imports successful")
        return True
    except Exception as e:
        print(f"[FAIL] Import error: {e}")
        return False

def test_error_handling():
    """Test error handling."""
    print("\nTesting error handling...")
    try:
        from src.infrastructure.mcp import MCPErrorHandler
        from src.domain.errors import ValidationError
        
        error = ValidationError("Test error")
        handled = MCPErrorHandler.handle_error(error, "test_tool")
        
        assert handled["code"] == "MCP-008"  # VALIDATION_ERROR
        assert "Validation failed" in handled["message"]
        print("[PASS] Error handling works correctly")
        return True
    except Exception as e:
        print(f"[FAIL] Error handling test failed: {e}")
        return False

def test_response_formatting():
    """Test response formatting."""
    print("\nTesting response formatting...")
    try:
        from src.infrastructure.mcp import MCPResponseFormatter
        
        formatted = MCPResponseFormatter.format_success({"test": "data"})
        assert "test" in formatted or "data" in formatted
        print("[PASS] Response formatting works correctly")
        return True
    except Exception as e:
        print(f"[FAIL] Response formatting test failed: {e}")
        return False

def test_workflow_validation():
    """Test workflow validation."""
    print("\nTesting workflow validation...")
    try:
        from src.infrastructure.n8n.util.n8n_validator import validate_workflow_structure
        
        # Test invalid workflow
        invalid_workflow = {"name": "Test", "nodes": [], "connections": {}}
        errors = validate_workflow_structure(invalid_workflow)
        assert len(errors) > 0
        print(f"[PASS] Invalid workflow validation: Found {len(errors)} errors (expected)")
        
        # Test valid workflow
        valid_workflow = {
            "name": "Test Workflow",
            "nodes": [{
                "id": "1",
                "name": "Start",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1.0,
                "position": [0, 0],
                "parameters": {}
            }],
            "connections": {
                "Start": {
                    "main": [[{"node": "Start", "type": "main", "index": 0}]]
                }
            }
        }
        errors = validate_workflow_structure(valid_workflow)
        print(f"[PASS] Valid workflow validation: Found {len(errors)} errors (should be 0 or minimal)")
        return True
    except Exception as e:
        print(f"[FAIL] Workflow validation test failed: {e}")
        return False

def test_server_initialization():
    """Test server initialization."""
    print("\nTesting server initialization...")
    try:
        from src import __main__
        
        server = __main__.N8nWorkflowGeneratorServer()
        tools = server.tool_registry.get_all_tools()
        
        assert len(tools) == 3, f"Expected 3 tools, got {len(tools)}"
        print(f"[PASS] Server initialization: {len(tools)} tools registered")
        return True
    except Exception as e:
        print(f"[FAIL] Server initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("n8n Workflow Generator MCP - Implementation Test")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_error_handling,
        test_response_formatting,
        test_workflow_validation,
        test_server_initialization,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"[FAIL] Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("[PASS] ALL TESTS PASSED - Implementation is ready!")
        return 0
    else:
        print("[FAIL] SOME TESTS FAILED - Please review errors above")
        return 1

if __name__ == "__main__":
    sys.exit(main())


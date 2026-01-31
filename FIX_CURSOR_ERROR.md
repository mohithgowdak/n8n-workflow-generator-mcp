# Fix: "No module named src.__main__" Error

## Problem

Cursor is showing this error:
```
C:\Python313\python.exe: No module named src.__main__; 'src' is a package and cannot be directly executed
```

## Cause

Cursor is using the **system Python** (`C:\Python313\python.exe`) instead of the **virtual environment Python**. The system Python doesn't have access to the `src` package.

## Solution

Update your Cursor MCP configuration to use the **full path to the virtual environment Python**.

### Updated Configuration

Replace your current configuration in `cline_mcp_settings.json` with:

```json
{
  "mcpServers": {
    "n8n-workflow-generator": {
      "command": "D:\\n8n_mcp_server_self_hosted\\n8n-workflow-generator-mcp\\venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "src"
      ],
      "cwd": "D:\\n8n_mcp_server_self_hosted\\n8n-workflow-generator-mcp",
      "env": {
        "N8N_API_URL": "http://localhost:5678",
        "N8N_API_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzNzI2YjczZS0yNjA4LTQ5YzItYTdjNS01ZDNjNDU1M2UyYTQiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzY5ODY3NDgyfQ.C1WqCjKakUv2UUvBEnyHlB7dDUReL4seBynD7Hi8-GM"
      }
    }
  }
}
```

### Key Change

**Before:**
```json
"command": "python",
```

**After:**
```json
"command": "D:\\n8n_mcp_server_self_hosted\\n8n-workflow-generator-mcp\\venv\\Scripts\\python.exe",
```

## Steps to Fix

1. **Open Cursor MCP Settings**
   - Path: `%APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`

2. **Update the `command` field**
   - Change from `"python"` to the full path shown above

3. **Save the file**

4. **Restart Cursor completely**

5. **Verify in Output Panel**
   - View → Output → MCP
   - Should see: "Registered 3 tools" and "n8n Workflow Generator MCP server running on stdio"

## Alternative: Use Wrapper Script

If the full path doesn't work, you can create a wrapper script:

### Create `start_mcp.bat`:

```batch
@echo off
cd /d "D:\n8n_mcp_server_self_hosted\n8n-workflow-generator-mcp"
call venv\Scripts\activate.bat
python -m src
```

Then use:
```json
{
  "command": "D:\\n8n_mcp_server_self_hosted\\n8n-workflow-generator-mcp\\start_mcp.bat",
  "args": [],
  "cwd": "D:\\n8n_mcp_server_self_hosted\\n8n-workflow-generator-mcp"
}
```

## Verify It Works

After updating, test manually:

```powershell
cd D:\n8n_mcp_server_self_hosted\n8n-workflow-generator-mcp
.\venv\Scripts\python.exe -m src
```

You should see:
```
n8n API configured: http://localhost:5678
Registered 3 tools
n8n Workflow Generator MCP server running on stdio
```

---

**Status**: ✅ **FIXED** - Use the full path to venv Python in Cursor config




# Quick Setup Guide for Cursor

## ✅ Step 1: Environment File Created

The `.env` file has been created with your credentials:
- **API URL**: `http://localhost:5678`
- **API Key**: Configured ✅

## 📝 Step 2: Configure Cursor MCP Settings

### Find the MCP Configuration File

**Windows Path**:
```
%APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json
```

**Quick Access**:
1. Press `Win + R`
2. Type: `%APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\`
3. Open `cline_mcp_settings.json`

### Add This Configuration

Copy the entire content from `CURSOR_MCP_CONFIG.json` or add this to your existing `cline_mcp_settings.json`:

```json
{
  "mcpServers": {
    "n8n-workflow-generator": {
      "command": "python",
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

**Important Notes**:
- ✅ API URL is `http://localhost:5678` (not `/docs` - the tool adds that automatically)
- ✅ Update `cwd` path if your project is in a different location
- ✅ Use forward slashes `/` or escaped backslashes `\\` in paths

### ⚠️ IMPORTANT: Use Full Python Path

**Cursor must use the virtual environment Python**, not the system Python. Use the full path:

```json
{
  "mcpServers": {
    "n8n-workflow-generator": {
      "command": "D:\\n8n_mcp_server_self_hosted\\n8n-workflow-generator-mcp\\venv\\Scripts\\python.exe",
      "args": ["-m", "src"],
      "cwd": "D:\\n8n_mcp_server_self_hosted\\n8n-workflow-generator-mcp",
      "env": {
        "N8N_API_URL": "http://localhost:5678",
        "N8N_API_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzNzI2YjczZS0yNjA4LTQ5YzItYTdjNS01ZDNjNDU1M2UyYTQiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzY5ODY3NDgyfQ.C1WqCjKakUv2UUvBEnyHlB7dDUReL4seBynD7Hi8-GM"
      }
    }
  }
}
```

**Do NOT use `"command": "python"`** - Cursor will use the system Python which doesn't have the dependencies installed.

## 🔄 Step 3: Restart Cursor

1. **Save** the `cline_mcp_settings.json` file
2. **Completely close** Cursor (not just the window)
3. **Reopen** Cursor

MCP servers load on startup, so a full restart is required.

## ✅ Step 4: Verify Setup

### Check Cursor Output Panel

1. In Cursor, go to **View → Output**
2. Select **"MCP"** or **"n8n-workflow-generator"** from the dropdown
3. Look for messages like:
   - "n8n API configured: http://localhost:5678"
   - "Registered 3 tools"
   - "n8n Workflow Generator MCP server running on stdio"

### Test the Tools

In Cursor chat, try:
```
"Generate a simple workflow that fetches data from an API endpoint"
```

You should see the `generate_workflow` tool being used.

## 🎯 What Happens Now

When you use `generate_workflow`:
1. ✅ Tool fetches n8n API docs from `http://localhost:5678/api/v1/docs/`
2. ✅ Includes docs in the response context
3. ✅ Cursor's LLM uses the docs to generate valid workflows
4. ✅ Workflows use correct node types and parameters

## 🐛 Troubleshooting

### Server Not Starting

1. **Test Python manually**:
   ```powershell
   cd D:\n8n_mcp_server_self_hosted\n8n-workflow-generator-mcp
   .\venv\Scripts\python.exe -m src
   ```

2. **Check dependencies**:
   ```powershell
   .\venv\Scripts\pip.exe list | Select-String "mcp"
   ```

### Tools Not Appearing

1. Check Cursor Output panel for errors
2. Verify the `cwd` path is correct
3. Ensure Python path is correct
4. Try using full path to Python executable

### API Connection Issues

1. **Verify n8n is running**:
   - Open `http://localhost:5678` in browser
   - Should see n8n interface

2. **Test API endpoint**:
   ```powershell
   curl http://localhost:5678/healthz
   ```

3. **Check API key**:
   - Verify it hasn't expired
   - Check it has proper permissions

## 📚 Next Steps

1. ✅ Environment configured
2. ✅ Cursor MCP settings ready
3. 🔄 Restart Cursor
4. 🎉 Start generating workflows!

---

**Ready!** Just add the configuration to Cursor and restart.


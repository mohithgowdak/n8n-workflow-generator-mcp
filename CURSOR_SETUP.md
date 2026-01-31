# Cursor MCP Server Setup Guide

## Quick Setup

### Step 1: Environment Configuration

The `.env` file has been created with your n8n credentials:
- **API URL**: `http://localhost:5678`
- **API Key**: (configured)

**Note**: The API URL should be `http://localhost:5678` (not the `/docs` endpoint). The tool automatically appends `/api/v1/docs/` when fetching documentation.

### Step 2: Configure Cursor MCP Settings

1. **Open Cursor Settings**
   - Press `Ctrl+,` (Windows) or `Cmd+,` (Mac)
   - Or go to: File → Preferences → Settings

2. **Navigate to MCP Settings**
   - Search for "MCP" in settings
   - Or manually navigate to the MCP configuration file

3. **Find the MCP Configuration File**

   **Windows**: 
   ```
   %APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json
   ```
   
   **Mac/Linux**: 
   ```
   ~/.config/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
   ```

4. **Add the Server Configuration**

   Open the file and add/update the `mcpServers` section:

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

   **Important**: 
   - Update the `cwd` path to match your actual project location
   - The `cwd` should point to the `n8n-workflow-generator-mcp` directory
   - Use forward slashes `/` or escaped backslashes `\\` in the path

### Step 3: Verify Python Path

Make sure Cursor can find Python. You can:

1. **Use full path to Python** (recommended):
   ```json
   {
     "command": "D:\\n8n_mcp_server_self_hosted\\n8n-workflow-generator-mcp\\venv\\Scripts\\python.exe",
     "args": ["-m", "src"],
     "cwd": "D:\\n8n_mcp_server_self_hosted\\n8n-workflow-generator-mcp"
   }
   ```

2. **Or ensure Python is in PATH**:
   - The virtual environment Python should work if `venv` is activated
   - Or use system Python if it's in your PATH

### Step 4: Restart Cursor

After adding the configuration:
1. **Save** the MCP settings file
2. **Restart Cursor** completely (close and reopen)
3. MCP servers load on startup

### Step 5: Verify Connection

1. **Check Cursor Output Panel**
   - View → Output
   - Select "MCP" or "n8n-workflow-generator" from the dropdown
   - Look for connection messages

2. **Test the Tools**
   - In Cursor chat, you should see 3 tools available:
     - `generate_workflow`
     - `validate_workflow`
     - `deploy_workflow`

3. **Try a Test Command**
   ```
   "Generate a simple workflow that fetches data from an API"
   ```

## Configuration Details

### Environment Variables

The server uses these environment variables (set in `.env` or Cursor config):

- **N8N_API_URL**: Base URL of your n8n instance (e.g., `http://localhost:5678`)
- **N8N_API_KEY**: Your n8n API key (JWT token)
- **LOG_LEVEL**: Logging level (default: `info`)

### API Documentation

The tool automatically fetches n8n API documentation from:
```
{N8N_API_URL}/api/v1/docs/
```

So with `N8N_API_URL=http://localhost:5678`, it will fetch from:
```
http://localhost:5678/api/v1/docs/
```

## Troubleshooting

### Server Won't Start

1. **Check Python Path**
   ```bash
   # Test if Python works
   cd D:\n8n_mcp_server_self_hosted\n8n-workflow-generator-mcp
   .\venv\Scripts\python.exe -m src
   ```

2. **Check Dependencies**
   ```bash
   .\venv\Scripts\pip.exe list | findstr mcp
   ```

3. **Check Logs**
   - Look in Cursor's Output panel
   - Check for error messages

### Tools Not Appearing

1. **Verify Server is Running**
   - Check Cursor's Output panel for MCP messages
   - Look for "Registered 3 tools" message

2. **Check Configuration**
   - Verify the `cwd` path is correct
   - Ensure Python path is correct
   - Check environment variables are set

3. **Restart Cursor**
   - Sometimes a full restart is needed

### API Connection Issues

1. **Verify n8n is Running**
   ```bash
   # Test n8n API
   curl http://localhost:5678/healthz
   ```

2. **Check API Key**
   - Verify the API key is valid
   - Check it hasn't expired
   - Ensure it has proper permissions

3. **Test API Connection**
   ```bash
   # Test with curl
   curl -H "X-N8N-API-KEY: YOUR_API_KEY" http://localhost:5678/api/v1/workflows
   ```

### Documentation Not Loading

If API docs can't be fetched:
- The tool will still work but without API documentation
- Check that n8n is running
- Verify the API URL is correct
- Check network connectivity

## Example Usage

Once configured, you can use the tools in Cursor:

### Generate Workflow
```
"Generate a workflow that:
1. Fetches data from https://api.example.com/data
2. Transforms the data
3. Saves it to a database"
```

### Validate Workflow
```
"Validate this workflow: {workflow_json}"
```

### Deploy Workflow
```
"Deploy this workflow to n8n and activate it: {workflow_json}"
```

## Next Steps

1. ✅ Environment configured (`.env` file)
2. ✅ Cursor MCP settings configured
3. ✅ Server ready to start
4. 🔄 Test with a simple workflow generation

---

**Status**: Ready to use! Configure Cursor MCP settings and restart Cursor.




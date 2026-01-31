# How to Start the n8n Workflow Generator MCP Server

## Quick Start

### 1. Prerequisites

- Python 3.13+ installed
- Virtual environment activated
- Dependencies installed

### 2. Start the Server

```bash
# Navigate to project directory
cd n8n-workflow-generator-mcp

# Activate virtual environment (if not already activated)
.\venv\Scripts\Activate.ps1  # Windows PowerShell
# OR
source venv/bin/activate      # Linux/Mac

# Start the server
python -m src
```

The server will start and run on stdio (standard input/output), which is how MCP servers communicate with Cursor.

## Configuration (Optional)

### For Deployment Features

If you want to deploy workflows to an n8n instance, create a `.env` file in the project root:

```bash
# .env file
N8N_API_URL=http://localhost:5678
N8N_API_KEY=your-api-key-here
```

**Note**: Without n8n API configuration, the server works in **validation-only mode**:
- ✅ `validate_workflow` - Fully functional
- ✅ `generate_workflow` - Available (LLM integration needed)
- ❌ `deploy_workflow` - Requires n8n API configuration

### Getting n8n API Key

1. Open your n8n instance
2. Go to Settings → API
3. Create a new API key
4. Copy the key to your `.env` file

## Using with Cursor

### 1. Configure Cursor MCP Settings

Add the server to your Cursor MCP configuration:

**Windows**: `%APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`

**Mac/Linux**: `~/.config/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

### 2. Add Server Configuration

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
- The API URL should be `http://localhost:5678` (not the `/docs` endpoint)
- The tool automatically fetches docs from `/api/v1/docs/`

### 3. Restart Cursor

After adding the configuration, restart Cursor to load the MCP server.

### 4. Verify Server is Running

In Cursor, you should see the server connected and 3 tools available:
- `generate_workflow`
- `validate_workflow`
- `deploy_workflow`

## Testing the Server

### Test Locally

```bash
# Run the test script
python test_implementation.py

# List available tools
python list_tools.py
```

### Expected Output

When the server starts, you should see:
```
n8n API not configured. Only workflow generation and validation available.
n8n API not configured (deployment features disabled)
Registered 3 tools
n8n Workflow Generator MCP server running on stdio
```

## Usage Examples

### 1. Generate a Workflow

In Cursor, you can now ask:
```
"Generate a workflow that fetches data from an API endpoint and saves it to a file"
```

The `generate_workflow` tool will be called with your prompt.

### 2. Validate a Workflow

```
"Validate this workflow: {workflow_json}"
```

The `validate_workflow` tool will check the workflow structure.

### 3. Deploy a Workflow

```
"Deploy this workflow to n8n and activate it: {workflow_json}"
```

The `deploy_workflow` tool will deploy the workflow to your n8n instance.

## Troubleshooting

### Server Won't Start

1. **Check Python version**:
   ```bash
   python --version  # Should be 3.13+
   ```

2. **Check dependencies**:
   ```bash
   pip list | grep mcp
   ```

3. **Check virtual environment**:
   ```bash
   which python  # Should point to venv
   ```

### Tools Not Appearing in Cursor

1. **Check MCP configuration** - Ensure the path is correct
2. **Restart Cursor** - MCP servers load on startup
3. **Check server logs** - Look for errors in Cursor's output panel

### n8n API Connection Issues

1. **Verify API URL** - Should be `http://your-n8n-instance:5678`
2. **Check API key** - Ensure it's valid and has proper permissions
3. **Test connection** - Use `curl` or `httpx` to test the API endpoint

## Development Mode

For development, you can run the server directly:

```bash
# Run with verbose logging
python -m src

# Or use Python directly
python src/__main__.py
```

## Next Steps

1. **Configure n8n API** (optional) - For deployment features
2. **Test tools** - Try generating, validating, and deploying workflows
3. **Integrate LLM** - Connect `generate_workflow` to Cursor's LLM for full functionality

## Support

If you encounter issues:
1. Check the logs in Cursor's output panel
2. Run `python test_implementation.py` to verify setup
3. Check that all dependencies are installed: `pip install -r requirements.txt`

---

**Ready to start?** Run `python -m src` and configure Cursor to use the MCP server!


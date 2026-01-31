# n8n API Documentation Integration

## Overview

The `generate_workflow` tool now automatically fetches and includes n8n API documentation from `http://localhost:5678/api/v1/docs/` (or your configured n8n instance) to guide workflow generation.

## How It Works

### 1. Automatic Documentation Fetching

When `generate_workflow` is called:
- The tool automatically fetches n8n API documentation from `/api/v1/docs/`
- The documentation is formatted and included in the response context
- Cursor's LLM receives both the user prompt AND the API documentation

### 2. Documentation Format

The fetched documentation includes:
- **API Endpoints**: All available n8n API endpoints
- **Node Types**: Information about available node types
- **Parameters**: Required and optional parameters for each node
- **Schemas**: Data structures used by the API
- **Examples**: Request/response formats

### 3. Response Structure

The `generate_workflow` tool now returns:

```json
{
  "error": null,
  "context": {
    "user_prompt": "Create a workflow that...",
    "workflow_name": "My Workflow",
    "n8n_api_docs_available": true,
    "n8n_api_docs_url": "http://localhost:5678/api/v1/docs",
    "n8n_api_docs": "...formatted documentation..."
  },
  "workflow": {...},
  "instructions": {
    "message": "Use the provided n8n API documentation...",
    "requirements": [...],
    "api_docs_reference": "http://localhost:5678/api/v1/docs/"
  }
}
```

## Configuration

### Setting n8n API URL

The documentation fetcher uses the same `N8N_API_URL` environment variable:

```env
N8N_API_URL=http://localhost:5678
N8N_API_KEY=your-api-key
```

### Documentation Endpoint

The tool automatically constructs the docs URL:
- Base URL: `http://localhost:5678`
- Docs Endpoint: `http://localhost:5678/api/v1/docs/`

## Features

### ✅ Automatic Fetching
- Documentation is fetched automatically when generating workflows
- No manual configuration needed

### ✅ Caching
- Documentation is cached to avoid repeated fetches
- Cache can be cleared if needed

### ✅ Error Handling
- Gracefully handles cases where docs are unavailable
- Falls back to basic workflow generation if docs can't be fetched

### ✅ Formatting
- OpenAPI/Swagger format is parsed and formatted for LLM consumption
- Includes structured information about endpoints, parameters, and schemas

## Usage

### In Cursor

When you ask Cursor to generate a workflow:

```
"Generate a workflow that fetches data from an API and saves it to a database"
```

The tool will:
1. Fetch n8n API documentation
2. Include it in the response context
3. Cursor's LLM will use the docs to generate a valid workflow

### Example Response

The LLM receives:
- Your prompt
- n8n API documentation (formatted)
- Instructions to use the docs
- Reference URL for full documentation

## Implementation Details

### Files

- **`n8n_docs_fetcher.py`**: Utility to fetch and format API docs
- **`workflow_tools.py`**: Updated `generate_workflow` handler to include docs

### Key Components

1. **N8nDocsFetcher**: Fetches docs from n8n API
2. **Formatting**: Converts OpenAPI/Swagger to LLM-friendly format
3. **Caching**: Reduces redundant API calls
4. **Integration**: Seamlessly included in workflow generation

## Benefits

1. **Accurate Workflows**: LLM has access to actual n8n API structure
2. **Valid Node Types**: Ensures generated nodes exist in n8n
3. **Correct Parameters**: Uses proper parameter names and types
4. **Up-to-Date**: Always uses current n8n API documentation
5. **No Manual Lookup**: Everything is automatic

## Troubleshooting

### Docs Not Available

If the documentation endpoint is unavailable:
- The tool will still work but without API docs
- A warning will be logged
- Basic workflow generation will proceed

### Timeout Issues

If fetching times out:
- Check that n8n is running
- Verify the API URL is correct
- Check network connectivity

### Cache Issues

To clear the documentation cache:
```python
from src.infrastructure.n8n.util.n8n_docs_fetcher import N8nDocsFetcher
fetcher = N8nDocsFetcher("http://localhost:5678")
fetcher.clear_cache()
```

## Future Enhancements

- [ ] Support for custom documentation endpoints
- [ ] Documentation versioning
- [ ] More sophisticated caching strategies
- [ ] Documentation filtering (only relevant sections)
- [ ] Integration with n8n node registry

---

**Status**: ✅ **FULLY INTEGRATED**

The n8n API documentation is now automatically included in workflow generation!




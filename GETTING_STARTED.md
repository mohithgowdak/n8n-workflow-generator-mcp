# Getting Started

## Project Setup

### 1. Create Virtual Environment

```bash
cd n8n-workflow-generator-mcp
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
# Windows:
copy .env.example .env

# Linux/Mac:
cp .env.example .env
```

Edit `.env`:
```env
N8N_API_URL=http://localhost:5678
N8N_API_KEY=your-api-key
LOG_LEVEL=info
```

### 4. Test Installation

```bash
python -m src
```

You should see: "n8n Workflow Generator MCP server running on stdio"

## Current Status

### ✅ Completed
- Project structure (Clean Architecture)
- Domain layer (types, errors)
- Basic MCP server setup
- Configuration management
- Logging infrastructure

### 🚧 Next Steps
1. Implement n8n API client
2. Implement n8n validator
3. Create workflow repository
4. Build workflow generation service
5. Create MCP tools
6. Implement tool handlers

## Development Workflow

1. **Study n8n-mcp code** - Understand validation and API patterns
2. **Translate to Python** - Adapt TypeScript code to Python
3. **Implement layer by layer** - Start with infrastructure, then services
4. **Test incrementally** - Test each component as you build

## Reference Documents

- `PYTHON_CLEAN_ARCHITECTURE.md` - Architecture details
- `CURSOR_LLM_INTEGRATION.md` - How Cursor LLM integration works
- `ARCHITECTURE_REUSE_RESEARCH.md` - What to reuse from n8n-mcp



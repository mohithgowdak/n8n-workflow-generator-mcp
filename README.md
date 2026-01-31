# n8n Workflow Generator MCP Server

A Model Context Protocol (MCP) server that generates n8n workflows from natural language prompts using Cursor's built-in LLM.

## Overview

This MCP server enables developers to create n8n workflows by simply describing what they want in natural language. Cursor's LLM uses MCP tools to generate complete, validated workflows ready for deployment.

## Features

- 🚀 **Prompt → Workflow**: Generate complete n8n workflows from natural language
- ✅ **Automatic Validation**: Validates workflows before deployment
- 🔧 **Clean Architecture**: Professional, scalable code structure
- 🐍 **Python**: Built with async Python and type safety
- 🤖 **AI Agent Optimized**: Tools designed for Cursor's LLM

## Architecture

Built with Clean Architecture principles:
- **Domain Layer**: Core business entities and protocols
- **Infrastructure Layer**: n8n API, MCP tools, validation
- **Service Layer**: Workflow generation orchestration
- **MCP Layer**: Tool definitions and handlers

## Quick Start

### Prerequisites

- Python 3.8+
- n8n instance (optional, for deployment)
- Cursor IDE (for MCP integration)

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd n8n-workflow-generator-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file:

```env
# n8n API (optional, for deployment)
N8N_API_URL=http://localhost:5678
N8N_API_KEY=your-api-key

# Logging
LOG_LEVEL=info
```

### Running

```bash
# Run MCP server
python -m src
```

### Cursor Integration

Add to Cursor's MCP configuration:

```json
{
  "mcpServers": {
    "n8n-workflow-generator": {
      "command": "python",
      "args": ["-m", "src"],
      "cwd": "/path/to/n8n-workflow-generator-mcp",
      "env": {
        "N8N_API_URL": "http://localhost:5678",
        "N8N_API_KEY": "your-api-key"
      }
    }
  }
}
```

## Available MCP Tools

- `generate_workflow` - Generate n8n workflow from prompt
- `validate_workflow` - Validate workflow structure
- `deploy_workflow` - Deploy workflow to n8n instance
- `refine_workflow` - Improve existing workflow
- `explain_workflow` - Explain what workflow does

## Project Structure

```
src/
├── domain/              # Domain layer - types, errors, protocols
├── infrastructure/      # Infrastructure - n8n API, tools, MCP
│   ├── n8n/           # n8n API integration
│   ├── tools/          # MCP tools
│   └── mcp/            # MCP protocol
└── services/            # Service layer - business logic
```

## Skills Demonstrated

- ✅ MCP Protocol Mastery
- ✅ AI Agent Integration
- ✅ Clean Architecture
- ✅ Python Expertise
- ✅ API Integration

## License

MIT License



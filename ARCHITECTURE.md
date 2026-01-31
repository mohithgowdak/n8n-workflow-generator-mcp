# Architecture Documentation

## Clean Architecture Structure

This project follows Clean Architecture principles with clear separation of concerns.

### Layer Structure

```
Domain Layer      → Core business entities, types, protocols (no dependencies)
Infrastructure    → External integrations (n8n API, MCP tools, validation)
Service Layer     → Business logic orchestration
MCP Layer         → Tool definitions, handlers, protocol implementation
```

## Project Structure

```
src/
├── domain/                  # Domain layer
│   ├── types.py            # Domain entities (Workflow, WorkflowNode)
│   └── errors.py           # Domain error types
│
├── infrastructure/         # Infrastructure layer
│   ├── n8n/               # n8n API integration
│   │   ├── repositories/  # Repository implementations
│   │   └── util/          # n8n utilities (API client, validator)
│   ├── tools/             # MCP tools
│   ├── mcp/               # MCP protocol
│   └── cache/             # Caching layer
│
└── services/               # Service layer
    └── workflow_generation_service.py
```

## Key Components

### Domain Layer
- **Types**: Workflow, WorkflowNode entities
- **Protocols**: WorkflowRepository interface
- **Errors**: Domain-specific error types

### Infrastructure Layer
- **n8n API Client**: HTTP client for n8n REST API
- **n8n Validator**: Workflow validation logic (adapted from n8n-mcp)
- **MCP Tools**: Tool definitions and handlers
- **Repositories**: n8n API repository implementations

### Service Layer
- **WorkflowGenerationService**: Main orchestrator
  - Coordinates LLM (via Cursor)
  - Validates workflows
  - Deploys to n8n

## Design Patterns

### Repository Pattern
- Abstracts data access
- Enables testing with mocks
- Clean separation of concerns

### Protocol-Based Interfaces
- Python `Protocol` for dependency inversion
- No concrete dependencies in domain layer

### Service Orchestration
- Service layer coordinates multiple repositories
- Business logic centralized
- Easy to test and maintain

## Technology Stack

- **Python 3.8+**: Async/await support
- **MCP SDK**: Model Context Protocol
- **Pydantic**: Validation and type safety
- **httpx**: Async HTTP client
- **python-dotenv**: Environment configuration

## Next Steps

1. Implement n8n API client (adapt from n8n-mcp)
2. Implement n8n validator (adapt from n8n-mcp)
3. Create workflow repository
4. Build workflow generation service
5. Create MCP tools
6. Implement tool handlers



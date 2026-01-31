# n8n Workflow Generator MCP Server - Architecture Diagram

## Complete System Architecture

```mermaid
graph TB
    subgraph "External Systems"
        Cursor[Cursor IDE<br/>LLM Integration]
        N8nAPI[n8n REST API<br/>localhost:5678]
        SQLite[(SQLite Database<br/>nodes.db)]
    end

    subgraph "MCP Server Entry Point"
        Main[__main__.py<br/>N8nWorkflowGeneratorServer]
        MCPProtocol[MCP Protocol Handler<br/>stdio_server]
    end

    subgraph "Domain Layer - Core Business Logic"
        DomainTypes[types.py<br/>Workflow<br/>WorkflowNode]
        DomainErrors[errors.py<br/>DomainError<br/>ValidationError<br/>ResourceNotFoundError<br/>N8nAPIError]
        DomainProtocol[WorkflowRepository<br/>Protocol Interface]
    end

    subgraph "Service Layer - Business Orchestration"
        WorkflowService[WorkflowGenerationService<br/>- Generate workflows<br/>- Validate workflows<br/>- Deploy workflows]
    end

    subgraph "Infrastructure Layer - External Integrations"
        subgraph "n8n Integration"
            N8nClient[n8n_api_client.py<br/>- create_workflow<br/>- get_workflow<br/>- update_workflow<br/>- delete_workflow<br/>- list_workflows<br/>- activate/deactivate<br/>- health_check]
            N8nValidator[n8n_validator.py<br/>- validate_workflow_structure<br/>- clean_workflow_for_create<br/>- clean_workflow_for_update]
            N8nDocsFetcher[n8n_docs_fetcher.py<br/>- fetch_docs<br/>- format_docs_for_llm]
            N8nConfig[n8n_config.py<br/>API Configuration]
            N8nRepo[n8n_workflow_repository.py<br/>Implements WorkflowRepository]
            BaseRepo[base_repository.py<br/>Base Repository]
        end

        subgraph "Database Layer"
            NodeRepo[node_repository.py<br/>- search_nodes<br/>- get_node<br/>FTS5 Search]
        end

        subgraph "MCP Protocol Layer"
            ToolRegistry[tool_registry.py<br/>ToolRegistry Singleton<br/>- register_tool<br/>- get_tool<br/>- get_all_tools]
            ProtocolUtils[protocol_utils.py<br/>- create_tool_from_definition<br/>- validate_tool_arguments<br/>- create_text_content<br/>- create_error_content]
            ErrorHandler[error_handler.py<br/>- handle_error<br/>- map_error_to_code<br/>MCPErrorCode Enum]
            ResponseFormatter[response_formatter.py<br/>Format responses]
        end

        subgraph "MCP Tools - 12 Tools"
            subgraph "Node Discovery Tools"
                Tool1[search_nodes<br/>Search n8n nodes]
                Tool2[get_node<br/>Get node details]
            end

            subgraph "Validation Tools"
                Tool3[validate_node<br/>Validate node config]
                Tool4[validate_workflow<br/>Validate workflow]
            end

            subgraph "Workflow Generation"
                Tool5[generate_workflow<br/>Generate from prompt]
            end

            subgraph "n8n API Management"
                Tool6[n8n_health_check<br/>Check API health]
                Tool7[n8n_list_workflows<br/>List workflows]
                Tool8[n8n_get_workflow<br/>Get workflow]
                Tool9[n8n_update_full_workflow<br/>Update workflow]
                Tool10[n8n_delete_workflow<br/>Delete workflow]
            end

            subgraph "Documentation"
                Tool11[tools_documentation<br/>Get tool docs]
            end
        end

        subgraph "Tool Registration Modules"
            WorkflowTools[workflow_tools.py<br/>register_workflow_tools]
            NodeTools[node_tools.py<br/>register_node_tools]
            ValidationTools[validation_tools.py<br/>register_validation_tools]
            N8nAPITools[n8n_api_tools.py<br/>register_n8n_api_tools]
            DocTools[documentation_tools.py<br/>register_documentation_tools]
        end

        subgraph "Utilities"
            Logger[logger.py<br/>Logger Singleton]
            Env[env.py<br/>Configuration<br/>Environment Variables]
            Cache[cache/<br/>Caching Layer]
        end
    end

    %% External Connections
    Cursor -->|MCP Protocol<br/>stdio| Main
    Main -->|HTTP Requests| N8nAPI
    NodeRepo -->|SQL Queries| SQLite
    WorkflowService -->|Uses| Cursor

    %% Domain Layer Connections
    DomainTypes -.->|Used by| WorkflowService
    DomainErrors -.->|Raised by| WorkflowService
    DomainProtocol -.->|Implemented by| N8nRepo

    %% Service Layer Connections
    Main --> WorkflowService
    WorkflowService --> N8nRepo
    WorkflowService --> N8nValidator

    %% Infrastructure Layer Connections
    Main --> ToolRegistry
    Main --> N8nClient
    Main --> NodeRepo
    N8nRepo --> N8nClient
    N8nRepo --> N8nValidator
    N8nRepo --> BaseRepo
    BaseRepo --> N8nClient
    BaseRepo --> Logger

    %% Tool Registration
    WorkflowTools --> ToolRegistry
    NodeTools --> ToolRegistry
    ValidationTools --> ToolRegistry
    N8nAPITools --> ToolRegistry
    DocTools --> ToolRegistry

    %% Tool Handlers
    Tool1 --> NodeRepo
    Tool2 --> NodeRepo
    Tool3 --> NodeRepo
    Tool4 --> N8nValidator
    Tool5 --> WorkflowService
    Tool5 --> N8nDocsFetcher
    Tool6 --> N8nClient
    Tool7 --> N8nRepo
    Tool8 --> N8nRepo
    Tool9 --> N8nRepo
    Tool10 --> N8nRepo
    Tool11 --> ToolRegistry

    %% MCP Protocol Flow
    Main --> MCPProtocol
    MCPProtocol --> ProtocolUtils
    ProtocolUtils --> ToolRegistry
    ProtocolUtils --> ErrorHandler
    ErrorHandler --> DomainErrors

    %% Configuration
    Env --> Main
    Env --> N8nClient
    N8nConfig --> N8nClient

    %% Logging
    Logger -.->|Used by| Main
    Logger -.->|Used by| WorkflowService
    Logger -.->|Used by| N8nRepo
    Logger -.->|Used by| ToolRegistry

    %% Styling
    classDef domainLayer fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef serviceLayer fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef infraLayer fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef toolLayer fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef external fill:#fce4ec,stroke:#880e4f,stroke-width:2px

    class DomainTypes,DomainErrors,DomainProtocol domainLayer
    class WorkflowService serviceLayer
    class N8nClient,N8nValidator,N8nRepo,NodeRepo,ToolRegistry,ProtocolUtils,ErrorHandler infraLayer
    class Tool1,Tool2,Tool3,Tool4,Tool5,Tool6,Tool7,Tool8,Tool9,Tool10,Tool11 toolLayer
    class Cursor,N8nAPI,SQLite external
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant User
    participant Cursor
    participant MCP_Server
    participant Tool_Registry
    participant Tool_Handler
    participant Service
    participant Repository
    participant N8n_API
    participant SQLite_DB

    User->>Cursor: Request workflow generation
    Cursor->>MCP_Server: call_tool("generate_workflow", args)
    MCP_Server->>Tool_Registry: get_tool("generate_workflow")
    Tool_Registry-->>MCP_Server: ToolDefinition
    MCP_Server->>Tool_Handler: validate_arguments(args)
    Tool_Handler->>Service: generate_workflow(prompt)
    Service->>N8n_API: fetch_api_docs()
    N8n_API-->>Service: OpenAPI docs
    Service->>Cursor: Request LLM generation (with docs context)
    Cursor-->>Service: Generated workflow JSON
    Service->>Service: validate_workflow(workflow)
    Service-->>Tool_Handler: workflow JSON
    Tool_Handler-->>MCP_Server: JSON response
    MCP_Server-->>Cursor: MCP response
    Cursor-->>User: Workflow generated

    User->>Cursor: Search for nodes
    Cursor->>MCP_Server: call_tool("search_nodes", {query: "webhook"})
    MCP_Server->>Tool_Registry: get_tool("search_nodes")
    Tool_Registry-->>MCP_Server: ToolDefinition
    MCP_Server->>Tool_Handler: search_nodes_handler(args)
    Tool_Handler->>SQLite_DB: search_nodes(query, limit)
    SQLite_DB-->>Tool_Handler: Results array
    Tool_Handler-->>MCP_Server: JSON response
    MCP_Server-->>Cursor: MCP response
    Cursor-->>User: Node search results

    User->>Cursor: Deploy workflow
    Cursor->>MCP_Server: call_tool("deploy_workflow", {workflow})
    MCP_Server->>Tool_Registry: get_tool("deploy_workflow")
    Tool_Registry-->>MCP_Server: ToolDefinition
    MCP_Server->>Tool_Handler: deploy_workflow_handler(args)
    Tool_Handler->>Service: deploy_workflow(workflow)
    Service->>Repository: create(workflow)
    Repository->>N8n_API: POST /workflows
    N8n_API-->>Repository: Created workflow
    Repository-->>Service: Workflow object
    Service-->>Tool_Handler: Deployment result
    Tool_Handler-->>MCP_Server: JSON response
    MCP_Server-->>Cursor: MCP response
    Cursor-->>User: Workflow deployed
```

## Component Interaction Diagram

```mermaid
graph LR
    subgraph "Request Flow"
        A[User Request] --> B[Cursor IDE]
        B --> C[MCP Server]
        C --> D[Tool Registry]
        D --> E[Tool Handler]
    end

    subgraph "Tool Categories"
        E --> F[Node Tools]
        E --> G[Validation Tools]
        E --> H[Workflow Tools]
        E --> I[n8n API Tools]
        E --> J[Documentation Tools]
    end

    subgraph "Data Sources"
        F --> K[Node Repository]
        G --> K
        G --> L[Workflow Validator]
        H --> M[Workflow Service]
        I --> N[Workflow Repository]
        J --> D
    end

    subgraph "External Systems"
        K --> O[(SQLite DB)]
        M --> P[Cursor LLM]
        N --> Q[n8n API]
    end

    subgraph "Response Flow"
        E --> R[Error Handler]
        E --> S[Response Formatter]
        S --> T[MCP Protocol]
        T --> B
        B --> A
    end

    style A fill:#e3f2fd
    style B fill:#f3e5f5
    style C fill:#e8f5e9
    style D fill:#fff3e0
    style E fill:#fce4ec
```

## Layer Dependencies Diagram

```mermaid
graph TD
    subgraph "Layer 1: Domain Layer (No Dependencies)"
        D1[Domain Types<br/>Workflow, WorkflowNode]
        D2[Domain Errors<br/>Error Classes]
        D3[Domain Protocols<br/>WorkflowRepository Interface]
    end

    subgraph "Layer 2: Infrastructure Layer (Depends on Domain)"
        I1[n8n API Client<br/>HTTP Client]
        I2[n8n Validator<br/>Validation Logic]
        I3[n8n Repository<br/>Implements WorkflowRepository]
        I4[Node Repository<br/>SQLite Access]
        I5[Tool Registry<br/>Tool Management]
        I6[MCP Protocol Utils<br/>Protocol Helpers]
    end

    subgraph "Layer 3: Service Layer (Depends on Infrastructure & Domain)"
        S1[WorkflowGenerationService<br/>Business Logic]
    end

    subgraph "Layer 4: MCP Tools (Depends on Service & Infrastructure)"
        T1[12 MCP Tools<br/>Tool Handlers]
    end

    subgraph "Layer 5: MCP Server (Depends on All Layers)"
        M1[MCP Server<br/>Entry Point]
    end

    D1 --> I3
    D2 --> I3
    D3 --> I3
    D1 --> S1
    D2 --> S1
    D3 --> S1

    I1 --> I3
    I2 --> I3
    I3 --> S1
    I4 --> T1
    I5 --> T1
    I6 --> T1

    S1 --> T1
    I3 --> T1

    T1 --> M1
    I5 --> M1
    S1 --> M1

    style D1 fill:#e1f5ff
    style D2 fill:#e1f5ff
    style D3 fill:#e1f5ff
    style I1 fill:#e8f5e9
    style I2 fill:#e8f5e9
    style I3 fill:#e8f5e9
    style I4 fill:#e8f5e9
    style I5 fill:#e8f5e9
    style I6 fill:#e8f5e9
    style S1 fill:#f3e5f5
    style T1 fill:#fff3e0
    style M1 fill:#fce4ec
```

## Tool Registration Flow

```mermaid
graph TB
    Start[Server Initialization] --> CheckEnv{Check Environment}
    CheckEnv -->|n8n API Configured| InitN8n[Initialize n8n Client]
    CheckEnv -->|No n8n API| SkipN8n[Skip n8n Tools]
    
    InitN8n --> InitRepo[Initialize Workflow Repository]
    InitRepo --> InitService[Initialize Workflow Service]
    InitService --> RegWorkflow[Register Workflow Tools]
    
    Start --> InitNodeDB[Initialize Node Database]
    InitNodeDB -->|DB Exists| InitNodeRepo[Initialize Node Repository]
    InitNodeDB -->|No DB| SkipNode[Skip Node Tools]
    
    InitNodeRepo --> RegNode[Register Node Tools]
    InitNodeRepo --> RegValidation[Register Validation Tools]
    
    Start --> RegDoc[Register Documentation Tools]
    
    InitN8n --> RegN8nAPI[Register n8n API Tools]
    
    RegWorkflow --> ToolRegistry[Tool Registry]
    RegNode --> ToolRegistry
    RegValidation --> ToolRegistry
    RegN8nAPI --> ToolRegistry
    RegDoc --> ToolRegistry
    
    ToolRegistry --> SetupHandlers[Setup MCP Handlers]
    SetupHandlers --> Ready[Server Ready<br/>12 Tools Registered]
    
    style Start fill:#e3f2fd
    style ToolRegistry fill:#fff3e0
    style Ready fill:#e8f5e9
```

## Error Handling Flow

```mermaid
graph TD
    A[Tool Handler Executes] --> B{Operation Success?}
    B -->|Yes| C[Return Success Response]
    B -->|No| D[Exception Caught]
    
    D --> E{Error Type?}
    E -->|DomainError| F[Error Handler]
    E -->|ValidationError| F
    E -->|ResourceNotFoundError| F
    E -->|N8nAPIError| F
    E -->|Other Exception| F
    
    F --> G[Map to MCP Error Code]
    G --> H[Format Error Response]
    H --> I[Log Error]
    I --> J[Return Error Response]
    
    C --> K[MCP Protocol Utils]
    J --> K
    K --> L[Format MCP Response]
    L --> M[Send to Cursor]
    
    style A fill:#e3f2fd
    style F fill:#ffebee
    style K fill:#fff3e0
    style M fill:#e8f5e9
```

## Complete Tool List with Dependencies

```mermaid
mindmap
  root((MCP Tools<br/>12 Tools))
    Node Discovery
      search_nodes
        NodeRepository
        SQLite FTS5
      get_node
        NodeRepository
        SQLite Query
    Validation
      validate_node
        NodeRepository
        n8n Validator
      validate_workflow
        n8n Validator
    Workflow Generation
      generate_workflow
        WorkflowService
        N8nDocsFetcher
        Cursor LLM
    n8n API Management
      n8n_health_check
        N8nApiClient
      n8n_list_workflows
        N8nWorkflowRepository
      n8n_get_workflow
        N8nWorkflowRepository
      n8n_update_full_workflow
        N8nWorkflowRepository
      n8n_delete_workflow
        N8nWorkflowRepository
    Documentation
      tools_documentation
        ToolRegistry
```

## Technology Stack Diagram

```mermaid
graph TB
    subgraph "Core Technologies"
        Python[Python 3.8+<br/>Async/Await]
        MCP[MCP SDK<br/>Model Context Protocol]
        Pydantic[Pydantic<br/>Validation & Types]
    end

    subgraph "HTTP & Networking"
        Httpx[httpx<br/>Async HTTP Client]
        Requests[HTTP Requests<br/>to n8n API]
    end

    subgraph "Data Storage"
        SQLite[SQLite<br/>FTS5 Full-Text Search]
        NodeDB[nodes.db<br/>Node Database]
    end

    subgraph "Configuration"
        DotEnv[python-dotenv<br/>Environment Variables]
        Config[env.py<br/>Configuration Management]
    end

    subgraph "Logging"
        Logger[Logger Singleton<br/>Centralized Logging]
    end

    subgraph "External Services"
        N8n[n8n REST API<br/>Workflow Management]
        CursorLLM[Cursor LLM<br/>Workflow Generation]
    end

    Python --> MCP
    Python --> Pydantic
    Python --> Httpx
    Python --> SQLite
    Python --> DotEnv
    
    Httpx --> Requests
    Requests --> N8n
    
    SQLite --> NodeDB
    
    DotEnv --> Config
    
    Python --> Logger
    
    MCP --> CursorLLM

    style Python fill:#3776ab,color:#fff
    style MCP fill:#4a90e2,color:#fff
    style Pydantic fill:#e92063,color:#fff
    style Httpx fill:#000000,color:#fff
    style SQLite fill:#003b57,color:#fff
```

---

## Architecture Principles

### 1. Clean Architecture
- **Domain Layer**: Pure business logic, no dependencies
- **Infrastructure Layer**: External integrations, depends on domain
- **Service Layer**: Business orchestration, depends on infrastructure
- **MCP Layer**: Protocol implementation, depends on all layers

### 2. Dependency Inversion
- Domain defines protocols (interfaces)
- Infrastructure implements protocols
- Service depends on protocols, not implementations

### 3. Singleton Pattern
- `ToolRegistry`: Single source of truth for tools
- `Logger`: Centralized logging

### 4. Repository Pattern
- Abstracts data access
- Enables testing with mocks
- Clean separation of concerns

### 5. Error Handling
- Domain-specific errors
- Mapped to MCP error codes
- Consistent error responses

---

## Key Components Summary

| Component | Purpose | Dependencies |
|-----------|---------|--------------|
| **N8nWorkflowGeneratorServer** | Main entry point | All layers |
| **ToolRegistry** | Tool management | None (singleton) |
| **WorkflowGenerationService** | Business logic | Repository, Validator |
| **N8nWorkflowRepository** | Data access | API Client, Validator |
| **NodeRepository** | Node database access | SQLite |
| **N8nApiClient** | HTTP client | httpx, config |
| **MCPProtocolUtils** | Protocol helpers | MCP SDK |
| **ErrorHandler** | Error mapping | Domain errors |

---

## Tool Count by Category

- **Node Discovery**: 2 tools
- **Validation**: 2 tools  
- **Workflow Generation**: 1 tool
- **n8n API Management**: 5 tools
- **Documentation**: 1 tool
- **Total**: 12 tools

---

*This architecture follows Clean Architecture principles with clear separation of concerns and dependency inversion.*


# n8n FlowForge — System Design Document (HLD + LLD)

> **Version:** 1.0
> **Date:** February 8, 2026
> **Status:** As-built analysis with forward-looking recommendations

---

# PART 1: HIGH-LEVEL DESIGN (HLD)

---

## 1.1 System Context

### Who interacts with this system, and how?

```
                    ┌─────────────────────────┐
                    │      DEVELOPER           │
                    │  (Primary Actor)         │
                    └───────────┬─────────────┘
                                │
                     Natural language prompts,
                     tool invocations, reviews
                                │
                                ▼
┌───────────────────────────────────────────────────────────┐
│                      CURSOR IDE                            │
│                                                            │
│  ┌──────────────┐    ┌──────────────────────────────────┐ │
│  │   LLM Engine │◄──►│  MCP Client (built-in)           │ │
│  │  (Claude,    │    │  - Discovers tools via list_tools │ │
│  │   GPT, etc.) │    │  - Invokes tools via call_tool   │ │
│  └──────────────┘    │  - Renders results to user       │ │
│                      └──────────────┬───────────────────┘ │
│                                     │                      │
└─────────────────────────────────────┼──────────────────────┘
                                      │
                           MCP Protocol (stdio)
                           JSON-RPC 2.0 over stdin/stdout
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────┐
│              n8n FlowForge MCP SERVER                        │
│                                                               │
│  Python 3.8+ async process, spawned by Cursor as child proc  │
│                                                               │
│  12 MCP tools │ Clean Architecture │ Pydantic validation     │
└────────────────────────────┬────────────────────────────────┘
                             │
                    ┌────────┴─────────┐
                    │                  │
            HTTP/REST (httpx)    SQLite (read-only)
                    │                  │
                    ▼                  ▼
         ┌──────────────────┐  ┌──────────────┐
         │   n8n Instance   │  │   nodes.db   │
         │  (self-hosted)   │  │  (FTS5 index │
         │                  │  │   1000+ nodes)│
         │  REST API v1     │  └──────────────┘
         │  Port 5678       │
         └──────────────────┘
```

### External Systems

| System | Protocol | Direction | Required? | Purpose |
|--------|----------|-----------|-----------|---------|
| **Cursor IDE** | MCP (stdio, JSON-RPC 2.0) | Bidirectional | Yes | Tool discovery, invocation, result rendering |
| **Cursor LLM** | Implicit (via MCP context) | Outbound context → Inbound generation | Yes (for generation) | Workflow JSON generation from natural language |
| **n8n Instance** | HTTP REST API v1 | Outbound | No (optional) | Workflow CRUD, deployment, activation |
| **nodes.db** | SQLite 3 (FTS5) | Read-only | No (optional) | Node search, schema lookup, validation reference |
| **OpenAPI Docs Endpoint** | HTTP GET | Outbound | No (optional) | Fetch n8n API docs for LLM context enrichment |

---

## 1.2 Component Architecture

### Layer Map

```
┌────────────────────────────────────────────────────────────────────────────┐
│ LAYER 0: TRANSPORT                                                          │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ MCP Server (mcp.server.Server)                                       │   │
│  │ ├── list_tools() handler → returns tool definitions                  │   │
│  │ └── call_tool() handler → validates args → dispatches to handler     │   │
│  │                           → formats response → returns TextContent   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                          │                                   │
│                                          │ dispatches via ToolRegistry       │
│                                          ▼                                   │
├────────────────────────────────────────────────────────────────────────────┤
│ LAYER 1: TOOLS (Interface Adapters)                                         │
│                                                                              │
│  ┌────────────────┐ ┌───────────────┐ ┌────────────────┐ ┌──────────────┐  │
│  │ workflow_tools  │ │  node_tools   │ │validation_tools│ │ n8n_api_tools│  │
│  │                 │ │               │ │                │ │              │  │
│  │ generate_wf     │ │ search_nodes  │ │ validate_node  │ │ get_wf       │  │
│  │ validate_wf     │ │ get_node      │ │                │ │ list_wfs     │  │
│  │ deploy_wf       │ │               │ │                │ │ update_wf    │  │
│  │                 │ │               │ │                │ │ delete_wf    │  │
│  │                 │ │               │ │                │ │ health_check │  │
│  └───────┬─────────┘ └───────┬───────┘ └───────┬────────┘ └──────┬───────┘  │
│          │                   │                  │                 │          │
│  ┌───────┴───────────────────┴──────────────────┴─────────────────┘          │
│  │ documentation_tools (tools_documentation) — always available              │
│  └───────────────────────────────────────────────────────────────────────┐   │
│                                          │                               │   │
│                                          ▼                               │   │
├────────────────────────────────────────────────────────────────────────────┤
│ LAYER 2: SERVICES (Application/Use Cases)                                   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ WorkflowGenerationService                                            │   │
│  │ ├── generate_workflow(prompt, name?) → raises NotImplementedError    │   │
│  │ ├── validate_workflow(workflow_dict) → {valid, errors, warnings}     │   │
│  │ ├── deploy_workflow(workflow_dict, activate?) → deployed workflow    │   │
│  │ └── update_workflow(workflow_id, workflow_dict) → updated workflow   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                          │                                   │
│                                          ▼                                   │
├────────────────────────────────────────────────────────────────────────────┤
│ LAYER 3: INFRASTRUCTURE (Frameworks & Drivers)                              │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────┐          │
│  │ n8n Integration                                               │          │
│  │ ┌─────────────────────┐  ┌─────────────────────────────────┐ │          │
│  │ │ N8nWorkflowRepository│  │ N8nApiClient (httpx)            │ │          │
│  │ │ ├── create()         │──│ ├── create_workflow()           │ │          │
│  │ │ ├── get_by_id()      │  │ ├── get_workflow()              │ │          │
│  │ │ ├── update()         │  │ ├── update_workflow()           │ │          │
│  │ │ ├── delete()         │  │ ├── delete_workflow()           │ │          │
│  │ │ ├── list()           │  │ ├── list_workflows()            │ │          │
│  │ │ ├── activate()       │  │ ├── activate_workflow()         │ │          │
│  │ │ └── deactivate()     │  │ ├── deactivate_workflow()       │ │          │
│  │ └─────────────────────┘  │ └── health_check()              │ │          │
│  │                           └─────────────────────────────────┘ │          │
│  │ ┌─────────────────────┐  ┌─────────────────────────────────┐ │          │
│  │ │ N8nValidator         │  │ N8nDocsFetcher                  │ │          │
│  │ │ ├── validate_wf_     │  │ ├── fetch_docs(use_cache?)     │ │          │
│  │ │ │   structure()      │  │ ├── clear_cache()              │ │          │
│  │ │ ├── clean_for_create│  │ └── get_docs_url()             │ │          │
│  │ │ └── clean_for_update│  └─────────────────────────────────┘ │          │
│  │ └─────────────────────┘                                       │          │
│  └───────────────────────────────────────────────────────────────┘          │
│                                                                              │
│  ┌───────────────────────────┐  ┌─────────────────────────────────┐        │
│  │ NodeRepository (SQLite)    │  │ MCP Protocol Utilities          │        │
│  │ ├── search_nodes()         │  │ ├── MCPErrorHandler             │        │
│  │ ├── get_node()             │  │ │   └── handle_error()          │        │
│  │ └── close()                │  │ ├── MCPProtocolUtils             │        │
│  └───────────────────────────┘  │ │   ├── create_tool_from_def()  │        │
│                                  │ │   ├── create_success_content()│        │
│  ┌───────────────────────────┐  │ │   ├── create_error_content()  │        │
│  │ Cross-Cutting              │  │ │   └── validate_tool_arguments│        │
│  │ ├── Logger (singleton)     │  │ └── MCPResponseFormatter       │        │
│  │ ├── Config (env.py)        │  │     ├── format_json()          │        │
│  │ └── ToolRegistry (single.) │  │     ├── format_error()         │        │
│  └───────────────────────────┘  │     └── format_success()        │        │
│                                  └─────────────────────────────────┘        │
├────────────────────────────────────────────────────────────────────────────┤
│ LAYER 4: DOMAIN (Enterprise Business Rules)                                 │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Entities:   Workflow, WorkflowNode                                   │   │
│  │ Protocols:  WorkflowRepository                                       │   │
│  │ Aliases:    WorkflowId = str, NodeId = str                           │   │
│  │ Errors:     DomainError → ValidationError, ResourceNotFoundError,    │   │
│  │             UnauthorizedError, RateLimitError, ConfigurationError,   │   │
│  │             IntegrationError, N8nAPIError, LLMError, MCPProtocolError│   │
│  │                                                                       │   │
│  │                    *** ZERO EXTERNAL DEPENDENCIES ***                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 1.3 Data Flows

### Flow 1: Workflow Generation (Primary Value Path)

```
 Developer                Cursor IDE               MCP Server            n8n Instance
    │                        │                         │                      │
    │  "Generate a workflow   │                         │                      │
    │   that does X"          │                         │                      │
    │───────────────────────►│                         │                      │
    │                        │                         │                      │
    │                        │  call_tool:             │                      │
    │                        │  generate_workflow      │                      │
    │                        │  {prompt: "...",        │                      │
    │                        │   workflow_name: "..."}  │                      │
    │                        │────────────────────────►│                      │
    │                        │                         │                      │
    │                        │                         │  GET /api/v1/docs    │
    │                        │                         │─────────────────────►│
    │                        │                         │                      │
    │                        │                         │  ◄── OpenAPI JSON ───│
    │                        │                         │                      │
    │                        │                         │  Format context:     │
    │                        │                         │  - User prompt       │
    │                        │                         │  - n8n API docs      │
    │                        │                         │  - Generation rules  │
    │                        │                         │  - Workflow template  │
    │                        │                         │                      │
    │                        │  ◄── TextContent ───────│                      │
    │                        │  (context + instructions │                      │
    │                        │   for LLM to generate)  │                      │
    │                        │                         │                      │
    │                        │  LLM reads context,     │                      │
    │                        │  generates workflow JSON │                      │
    │                        │                         │                      │
    │  ◄── "Here's the       │                         │                      │
    │      workflow JSON"     │                         │                      │
    │                        │                         │                      │
    │  "validate this"        │                         │                      │
    │───────────────────────►│                         │                      │
    │                        │  call_tool:             │                      │
    │                        │  validate_workflow      │                      │
    │                        │  {workflow: {...}}       │                      │
    │                        │────────────────────────►│                      │
    │                        │                         │                      │
    │                        │                         │  validate_workflow_  │
    │                        │                         │  structure()         │
    │                        │                         │  ├─ Check name       │
    │                        │                         │  ├─ Check nodes[]    │
    │                        │                         │  ├─ Check connections│
    │                        │                         │  ├─ Validate types   │
    │                        │                         │  └─ Check triggers   │
    │                        │                         │                      │
    │                        │  ◄── {valid: true/false,│                      │
    │                        │       errors: [...]}    │                      │
    │                        │                         │                      │
    │  ◄── Validation result  │                         │                      │
    │                        │                         │                      │
    │  "deploy it"            │                         │                      │
    │───────────────────────►│                         │                      │
    │                        │  call_tool:             │                      │
    │                        │  deploy_workflow        │                      │
    │                        │  {workflow: {...},       │                      │
    │                        │   activate: true}       │                      │
    │                        │────────────────────────►│                      │
    │                        │                         │                      │
    │                        │                         │  validate again      │
    │                        │                         │  clean_for_create()  │
    │                        │                         │                      │
    │                        │                         │  POST /workflows     │
    │                        │                         │─────────────────────►│
    │                        │                         │                      │
    │                        │                         │  ◄── {id: "42", ..}──│
    │                        │                         │                      │
    │                        │                         │  POST /workflows/    │
    │                        │                         │  42/activate         │
    │                        │                         │─────────────────────►│
    │                        │                         │                      │
    │                        │                         │  ◄── activated ──────│
    │                        │                         │                      │
    │                        │  ◄── {id: "42",         │                      │
    │                        │       active: true}     │                      │
    │                        │                         │                      │
    │  ◄── "Deployed! ID: 42"│                         │                      │
    │                        │                         │                      │
```

### Flow 2: Node Discovery

```
 Developer            Cursor IDE            MCP Server           nodes.db
    │                    │                      │                    │
    │  "What nodes       │                      │                    │
    │   handle email?"   │                      │                    │
    │──────────────────►│                      │                    │
    │                    │  call_tool:          │                    │
    │                    │  search_nodes        │                    │
    │                    │  {query: "email",    │                    │
    │                    │   mode: "OR",        │                    │
    │                    │   limit: 20}         │                    │
    │                    │───────────────────►  │                    │
    │                    │                      │                    │
    │                    │                      │  FTS5 MATCH query  │
    │                    │                      │──────────────────►│
    │                    │                      │                    │
    │                    │                      │  ◄── rows ranked ──│
    │                    │                      │      by relevance  │
    │                    │                      │                    │
    │                    │                      │  _row_to_dict()    │
    │                    │                      │  for each result   │
    │                    │                      │                    │
    │                    │  ◄── {results: [...],│                    │
    │                    │       count: N}      │                    │
    │                    │                      │                    │
    │  ◄── "Found N      │                      │                    │
    │      email nodes"  │                      │                    │
```

### Flow 3: Error Propagation

```
 Tool Handler          Service Layer        Repository         API Client       n8n
    │                      │                    │                   │             │
    │  deploy(workflow)     │                    │                   │             │
    │─────────────────────►│                    │                   │             │
    │                      │  validate()        │                   │             │
    │                      │  ──── OK ────►     │                   │             │
    │                      │                    │                   │             │
    │                      │  create(workflow)   │                   │             │
    │                      │───────────────────►│                   │             │
    │                      │                    │  create_workflow() │             │
    │                      │                    │──────────────────►│             │
    │                      │                    │                   │  POST /wf   │
    │                      │                    │                   │────────────►│
    │                      │                    │                   │             │
    │                      │                    │                   │  ◄── 401 ───│
    │                      │                    │                   │             │
    │                      │                    │  ◄── N8nApiError ─│             │
    │                      │                    │      (status=401) │             │
    │                      │                    │                   │             │
    │                      │  ◄── Exception ────│                   │             │
    │                      │      propagated    │                   │             │
    │                      │                    │                   │             │
    │  ◄── Exception ──────│                    │                   │             │
    │      propagated      │                    │                   │             │
    │                      │                    │                   │             │
    │  MCPErrorHandler     │                    │                   │             │
    │  .handle_error()     │                    │                   │             │
    │  ├── map to MCP-010  │                    │                   │             │
    │  ├── format error    │                    │                   │             │
    │  └── return TextContent (isError=true)    │                   │             │
    │                      │                    │                   │             │
```

---

## 1.4 Non-Functional Requirements

### Current State (As-Built)

| Requirement | Target | Current Status | Notes |
|-------------|--------|----------------|-------|
| **Latency — Node search** | < 50ms | ~5-20ms | SQLite FTS5 is fast |
| **Latency — Workflow validation** | < 200ms | ~50-100ms | Pydantic + rule checks |
| **Latency — Workflow deploy** | < 3s | ~500ms-2s | Network-bound to n8n API |
| **Latency — Generate context** | < 5s | ~1-3s | OpenAPI fetch dominates |
| **Availability** | Matches Cursor uptime | Process lifecycle tied to Cursor | Dies when Cursor closes, restarts on reopen |
| **Throughput** | Single-user sufficient | ~10-50 tool calls/minute | Limited by async event loop, not a bottleneck |
| **Data consistency** | Eventual | Eventual | Node DB can be stale; n8n state is authoritative |
| **Security — Transport** | Local-only | stdio (no network exposure) | Correct for single-user |
| **Security — Auth** | API key in env | API key in .env, no rotation | Acceptable for dev, not for team |
| **Security — Secrets** | Not logged | Credentials not in tool responses | API key in headers only |
| **Reliability** | Graceful degradation | Partial — tools work independently | If n8n is down, generation/search still work |
| **Observability** | Structured logging | Basic stderr logging | No correlation IDs, no metrics |
| **Testability** | Protocol-based interfaces | Protocol exists, few tests | Architecture supports testing, tests are sparse |

### Production Targets (Phase 5)

| Requirement | Target | Implementation Path |
|-------------|--------|---------------------|
| **Latency — Generate context** | < 1s (cached) | In-memory TTL cache for OpenAPI docs |
| **Reliability — n8n reconnection** | Auto-retry with backoff | Retry decorator on N8nApiClient methods |
| **Observability** | Correlation IDs per tool call | Middleware in call_tool handler |
| **Security — Multi-user** | Instance profiles with separate keys | Connection profiles config file |
| **Data freshness** | Node DB < 24 hours stale | Background sync on server start |

---

---

# PART 2: LOW-LEVEL DESIGN (LLD)

---

## 2.1 Module Design — Detailed Breakdown

### Module: Domain Layer

```
src/domain/
├── types.py          # 2 dataclasses, 1 protocol, 2 type aliases
└── errors.py         # 10 exception classes (1 base + 9 specialized)
```

**Dependency rule:** This layer imports NOTHING from the rest of the codebase. Only stdlib `dataclasses`, `typing`.

**types.py — Full Schema:**

```python
@dataclass
class WorkflowNode:
    id: str                                  # UUID or sequential (e.g., "a1b2c3d4")
    name: str                                # Human label (e.g., "HTTP Request")
    type: str                                # Fully qualified (e.g., "n8n-nodes-base.httpRequest")
    typeVersion: int                         # Node schema version (e.g., 4)
    position: List[int]                      # Canvas [x, y] (e.g., [250, 300])
    parameters: Dict[str, Any]              # Node-specific config (varies per type)
    credentials: Optional[Dict[str, Any]]   # Credential refs (e.g., {"httpBasicAuth": {"id": "1"}})
    disabled: bool = False                  # Skipped during execution
    notes: Optional[str] = None             # Inline annotation
    continueOnFail: bool = False            # Continue pipeline on error
    retryOnFail: bool = False               # Auto-retry on error
    maxTries: Optional[int] = None          # Max retry attempts
    waitBetweenTries: Optional[int] = None  # Retry interval (milliseconds)

@dataclass
class Workflow:
    id: Optional[str] = None                # n8n-assigned (None before first deploy)
    name: str = ""                          # Required for creation
    nodes: List[WorkflowNode] = None        # Defaults to [] in __post_init__
    connections: Dict[str, Any] = None      # Defaults to {} in __post_init__
    settings: Optional[Dict[str, Any]]      # Workflow-level config
    active: bool = False                    # Is workflow enabled in n8n
    tags: Optional[List[str]] = None        # Categorization

class WorkflowRepository(Protocol):
    async def create(self, workflow: Workflow) -> Workflow
    async def find_by_id(self, workflow_id: str) -> Optional[Workflow]
    async def update(self, workflow_id: str, workflow: Workflow) -> Workflow
    async def delete(self, workflow_id: str) -> None
    async def list(self, **filters) -> List[Workflow]

# Type Aliases
WorkflowId = str
NodeId = str
```

**errors.py — Exception Hierarchy:**

```
Exception
└── DomainError (base)
    ├── ValidationError          # Malformed workflow/node data
    ├── ResourceNotFoundError    # Workflow/node ID doesn't exist
    ├── UnauthorizedError        # Bad or missing API key
    ├── RateLimitError           # n8n rate limit hit
    ├── ConfigurationError       # Missing env vars, bad config
    ├── IntegrationError         # Generic external system failure
    ├── N8nAPIError              # n8n-specific HTTP errors
    ├── LLMError                 # LLM service errors (unused currently)
    └── MCPProtocolError         # MCP protocol-level failures
```

---

### Module: Service Layer

```
src/services/
└── workflow_generation_service.py    # 1 class, 4 methods
```

**WorkflowGenerationService — Method Detail:**

| Method | Input | Output | Calls | Errors Raised | Notes |
|--------|-------|--------|-------|---------------|-------|
| `generate_workflow(prompt, name?)` | `str, Optional[str]` | `Dict[str, Any]` | Nothing | `NotImplementedError` | Placeholder. Actual generation happens in tool handler via LLM. |
| `validate_workflow(workflow)` | `Dict[str, Any]` | `{'valid': bool, 'errors': [], 'warnings': []}` | `validate_workflow_structure()` | None (errors in return value) | Pure validation, no side effects. |
| `deploy_workflow(workflow, activate?)` | `Dict[str, Any], bool` | `Dict[str, Any]` (created workflow) | `validate_workflow()` → `repository.create()` → `repository.activate()` | `ValidationError` | Validates before deploy. Activate is optional second step. |
| `update_workflow(id, workflow)` | `str, Dict[str, Any]` | `Dict[str, Any]` (updated workflow) | `validate_workflow()` → `repository.update()` | `ValidationError` | Validates before update. |

---

### Module: Infrastructure — n8n API Client

```
src/infrastructure/n8n/util/n8n_api_client.py    # 1 class, 9 methods
```

**N8nApiClient — Connection Configuration:**

```python
# Initialization
base_url:    str          # e.g., "http://localhost:5678" → normalized to ".../api/v1"
api_key:     str          # n8n API key
timeout:     float        # seconds (default: 30, converted from ms input)
max_retries: int          # default: 3 (not yet implemented in methods)

# httpx.AsyncClient config
headers = {
    "X-N8N-API-KEY": api_key,
    "Content-Type": "application/json"
}
timeout = httpx.Timeout(timeout_seconds)
```

**HTTP Endpoint Map:**

| Method | HTTP | Endpoint | Request Body | Response | Error Handling |
|--------|------|----------|-------------|----------|----------------|
| `health_check()` | GET | `/healthz` | None | `{status, n8nVersion, features}` | Falls back to `list_workflows(limit=1)` on failure |
| `create_workflow(wf)` | POST | `/workflows` | Workflow JSON | Created workflow | `N8nApiError(status_code, response)` |
| `get_workflow(id)` | GET | `/workflows/{id}` | None | Workflow JSON | `N8nApiError(status_code, response)` |
| `update_workflow(id, wf)` | PUT | `/workflows/{id}` | Workflow JSON | Updated workflow | Falls back to PATCH on 405 |
| `delete_workflow(id)` | DELETE | `/workflows/{id}` | None | Deletion confirmation | `N8nApiError(status_code, response)` |
| `list_workflows(limit?, cursor?)` | GET | `/workflows?limit=&cursor=` | None | `{data: [], nextCursor?}` | Handles list vs paginated format |
| `activate_workflow(id)` | POST | `/workflows/{id}/activate` | None | Activated workflow | `N8nApiError(status_code, response)` |
| `deactivate_workflow(id)` | POST | `/workflows/{id}/deactivate` | None | Deactivated workflow | `N8nApiError(status_code, response)` |

**Update fallback logic:**

```
update_workflow(id, workflow):
  try:
    PUT /workflows/{id}        ◄── Primary attempt
  except HTTP 405:
    PATCH /workflows/{id}      ◄── Fallback for older n8n versions
```

---

### Module: Infrastructure — Validator

```
src/infrastructure/n8n/util/n8n_validator.py    # 1 Pydantic model, 5 functions
```

**Validation Rules (in execution order within `validate_workflow_structure`):**

```
Rule 1:  name is present and non-empty
Rule 2:  nodes[] is present and non-empty
Rule 3:  at least one executable node (excludes sticky notes)
Rule 4:  connections{} is present
Rule 5:  single non-webhook node without connections → error
Rule 6:  multi-node workflow without connections → error
Rule 7:  disconnected nodes detected (except trigger nodes)
Rule 8:  each node passes Pydantic WorkflowNode validation
           ├── id: str (required)
           ├── name: str (required)
           ├── type: str (required)
           ├── typeVersion: float (required)
           ├── position: tuple[float, float] (required)
           └── parameters: Dict (required)
Rule 9:  node type format: must contain "." (package.nodeName format)
Rule 10: active workflows must have at least one enabled trigger node
```

**Workflow Cleaning Functions:**

`clean_workflow_for_create(workflow)` — Strips read-only fields before POST:

```
Removes: id, createdAt, updatedAt, versionId, meta, active, tags

Ensures settings defaults:
  executionOrder: "v1"
  saveDataErrorExecution: "all"
  saveDataSuccessExecution: "all"
  saveManualExecutions: true
  saveExecutionProgress: true
```

`clean_workflow_for_update(workflow)` — Strips computed fields before PUT/PATCH:

```
Removes: id, createdAt, updatedAt, versionId, versionCounter, meta,
         staticData, pinData, tags, description, isArchived,
         usedCredentials, sharedWithProjects, triggerCount, shared,
         active, activeVersionId, activeVersion

Settings whitelist:
  saveExecutionProgress, saveManualExecutions, saveDataErrorExecution,
  saveDataSuccessExecution, executionTimeout, errorWorkflow, timezone,
  executionOrder, callerPolicy, callerIds, timeSavedPerExecution,
  availableInMCP
```

---

### Module: Infrastructure — Node Repository

```
src/infrastructure/database/node_repository.py    # 1 class, 7 methods
```

**Search Modes — Query Translation:**

| Mode | Input | FTS5 Query | Example |
|------|-------|------------|---------|
| **OR** | `"email send"` | `"email send"` (default FTS5 OR) | Matches any word |
| **AND** | `"email send"` | `"email" AND "send"` | Matches all words |
| **FUZZY** | `"emal snd"` | `"emal*" OR "snd*"` | Wildcard prefix matching |

**Source Filtering SQL:**

| Source | WHERE clause appended |
|--------|----------------------|
| `all` | (none) |
| `core` | `AND (is_community = 0 OR is_community IS NULL)` |
| `community` | `AND is_community = 1` |
| `verified` | `AND is_community = 1 AND is_verified = 1` |

**Node Type Normalization:**

```
Input:  "n8n-nodes-base.httpRequest"     → "nodes-base.httpRequest"
Input:  "@n8n/n8n-nodes-langchain.agent" → "nodes-langchain.agent"
```

This normalization is applied to both search queries and get_node lookups, with a fallback to the original string if the normalized version doesn't match.

**Result Mapping (`_row_to_dict`):**

```python
{
    "nodeType":      row["node_type"],
    "displayName":   row["display_name"],
    "description":   row["description"],
    "category":      row["category"],
    "packageName":   row["package_name"],
    "properties":    json.loads(row["properties_schema"]),   # if standard/full
    "operations":    json.loads(row["operations"]),           # if standard/full
    "documentation": row["documentation"],                    # if available
    "isCommunity":   bool(row["is_community"]),
    "isVerified":    bool(row["is_verified"]),
    "authorName":    row["author_name"],
    "npmDownloads":  row["npm_downloads"],
    "isTrigger":     bool(row["is_trigger"]),
    "isWebhook":     bool(row["is_webhook"]),
    "isAITool":      bool(row["is_ai_tool"])
}
```

---

## 2.2 State Machine — Server Lifecycle

```
                    ┌─────────┐
                    │  INIT   │
                    └────┬────┘
                         │
            ┌────────────┼───────────────┐
            │            │               │
            ▼            ▼               ▼
     ┌────────────┐ ┌─────────┐ ┌──────────────┐
     │ Load Config│ │ Init DB │ │ Init n8n API │
     │  (env.py)  │ │(optional│ │  (optional)  │
     └─────┬──────┘ │ SQLite) │ └──────┬───────┘
           │        └────┬────┘        │
           │             │             │
           └──────┬──────┘             │
                  │                    │
                  ▼                    ▼
         ┌──────────────┐    ┌──────────────────┐
         │Register Tools │    │Create Repository │
         │(node, valid., │    │& Service         │
         │ docs — always)│    │(if API configured)│
         └───────┬───────┘    └────────┬─────────┘
                 │                     │
                 │     ┌───────────────┘
                 │     │
                 ▼     ▼
         ┌──────────────────┐
         │ Register n8n     │
         │ Tools (workflow, │
         │ api — if avail.) │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │ Setup MCP        │
         │ Handlers         │
         │ (list_tools,     │
         │  call_tool)      │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │    RUNNING       │◄──────────────────────┐
         │  (stdio loop)    │                       │
         │                  │   Process tool calls  │
         │  Waiting for     │   Return results      │
         │  JSON-RPC input  │───────────────────────┘
         └────────┬─────────┘
                  │
          KeyboardInterrupt
          or Cursor closes
                  │
                  ▼
         ┌──────────────────┐
         │   SHUTDOWN       │
         │                  │
         │ Close API client │
         │ Close DB conn    │
         │ Exit process     │
         └──────────────────┘
```

### Tool Call State Machine

```
              ┌──────────────────┐
              │  IDLE (waiting)   │
              └────────┬─────────┘
                       │
              call_tool JSON-RPC
                       │
                       ▼
              ┌──────────────────┐
              │ LOOKUP TOOL      │
              │ registry.get()   │
              └────┬────────┬────┘
                   │        │
              Found     Not Found
                   │        │
                   │        ▼
                   │   ┌──────────────┐
                   │   │ RETURN ERROR │
                   │   │ "Unknown     │
                   │   │  tool: ..."  │
                   │   └──────────────┘
                   ▼
              ┌──────────────────┐
              │ VALIDATE ARGS    │
              │ against schema   │
              └────┬────────┬────┘
                   │        │
               Valid     Invalid
                   │        │
                   │        ▼
                   │   ┌──────────────┐
                   │   │ RETURN ERROR │
                   │   │ MCP-002      │
                   │   └──────────────┘
                   ▼
              ┌──────────────────┐
              │ EXECUTE HANDLER  │
              │ await handler()  │
              └────┬────────┬────┘
                   │        │
              Success    Exception
                   │        │
                   ▼        ▼
      ┌────────────┐  ┌──────────────────┐
      │FORMAT RESULT│  │MCPErrorHandler   │
      │TextContent  │  │.handle_error()   │
      │isError=false│  │map to MCP code   │
      └─────┬──────┘  │TextContent       │
            │         │isError=true      │
            │         └──────┬───────────┘
            │                │
            └───────┬────────┘
                    │
                    ▼
           ┌──────────────────┐
           │ RETURN RESPONSE  │
           │ via JSON-RPC     │
           └────────┬─────────┘
                    │
                    ▼
           ┌──────────────────┐
           │  IDLE (waiting)   │
           └──────────────────┘
```

---

## 2.3 Complete Data Models

### Model 1: n8n Workflow JSON (as sent to / received from n8n API)

```json
{
  "id": "42",                              // string, n8n-assigned
  "name": "My Workflow",                   // string, required
  "active": false,                         // boolean
  "nodes": [                               // array, required, min 1
    {
      "id": "uuid-1234",                   // string, unique within workflow
      "name": "Webhook",                   // string, display label
      "type": "n8n-nodes-base.webhook",    // string, fully qualified
      "typeVersion": 2,                    // integer
      "position": [250, 300],              // [x, y] integers
      "parameters": {                      // object, node-specific
        "httpMethod": "POST",
        "path": "my-webhook",
        "responseMode": "onReceived"
      },
      "credentials": {},                   // object, optional
      "disabled": false,                   // boolean, default false
      "notes": "",                         // string, optional
      "continueOnFail": false,             // boolean, default false
      "retryOnFail": false,                // boolean, default false
      "maxTries": 3,                       // integer, optional
      "waitBetweenTries": 1000             // integer (ms), optional
    }
  ],
  "connections": {                         // object, required
    "Webhook": {                           // keyed by source node name
      "main": [                            // output type ("main" for data)
        [                                  // output index 0
          {
            "node": "HTTP Request",        // target node name
            "type": "main",                // connection type
            "index": 0                     // target input index
          }
        ]
      ]
    }
  },
  "settings": {                            // object, optional
    "executionOrder": "v1",
    "saveDataErrorExecution": "all",
    "saveDataSuccessExecution": "all",
    "saveManualExecutions": true,
    "saveExecutionProgress": true,
    "executionTimeout": 3600,
    "timezone": "America/New_York"
  },
  "tags": ["generated", "slack"],          // array of strings, optional
  "createdAt": "2026-02-08T10:00:00Z",    // ISO 8601, read-only
  "updatedAt": "2026-02-08T10:05:00Z"     // ISO 8601, read-only
}
```

### Model 2: Node Database Row (SQLite)

```
┌─────────────────────┬──────────┬──────────────────────────────────────────────────┐
│ Column              │ Type     │ Example Value                                     │
├─────────────────────┼──────────┼──────────────────────────────────────────────────┤
│ node_type (PK)      │ TEXT     │ "n8n-nodes-base.httpRequest"                     │
│ display_name        │ TEXT     │ "HTTP Request"                                   │
│ description         │ TEXT     │ "Makes an HTTP request and returns response"     │
│ category            │ TEXT     │ "Network"                                        │
│ package_name        │ TEXT     │ "n8n-nodes-base"                                 │
│ properties_schema   │ TEXT/JSON│ '{"method":{"type":"options",...},...}'           │
│ operations          │ TEXT/JSON│ '["GET","POST","PUT","DELETE","PATCH"]'           │
│ documentation       │ TEXT     │ "# HTTP Request\n\nMakes HTTP requests..."      │
│ version             │ INTEGER  │ 4                                                │
│ is_community        │ INTEGER  │ 0 (boolean: 0=core, 1=community)                │
│ is_verified         │ INTEGER  │ 0 (boolean: 0=no, 1=verified community)         │
│ author_name         │ TEXT     │ "n8n"                                            │
│ npm_downloads       │ INTEGER  │ 150000                                           │
│ is_trigger          │ INTEGER  │ 0 (boolean)                                      │
│ is_webhook          │ INTEGER  │ 0 (boolean)                                      │
│ is_ai_tool          │ INTEGER  │ 0 (boolean)                                      │
└─────────────────────┴──────────┴──────────────────────────────────────────────────┘

FTS5 Virtual Table (nodes_fts):
  Indexes: node_type, display_name, description, category, operations
  Joined to nodes table via: nodes_fts.rowid = nodes.rowid
```

### Model 3: MCP Tool Definition (Internal Registry)

```python
@dataclass
class ToolDefinition:
    name: str                    # "generate_workflow"
    description: str             # "Generate an n8n workflow from..."
    handler: Callable            # async function(arguments: Dict) -> str
    schema: Dict[str, Any]       # JSON Schema for input validation
```

### Model 4: MCP Error Response

```json
{
  "error": {
    "code": "MCP-008",
    "message": "Workflow validation failed: name is required",
    "details": {
      "error_type": "ValidationError",
      "tool": "deploy_workflow"
    }
  }
}
```

---

## 2.4 API Contracts — Every MCP Tool

### Tool 1: `generate_workflow`

```
INPUT:
  {
    "prompt": string (required)     — Natural language workflow description
    "workflow_name": string          — Optional name for the workflow
  }

OUTPUT (success):
  {
    "context": string               — Formatted generation context for LLM
    "workflow_structure": object     — Template structure hint
    "instructions": string          — Generation rules and constraints
    "api_docs": string | null       — n8n OpenAPI docs (if fetched)
  }

OUTPUT (error):
  {
    "error": {
      "code": "MCP-010",
      "message": "Failed to fetch n8n API docs: connection refused"
    }
  }

SIDE EFFECTS:
  - HTTP GET to {n8n_base_url}/api/v1/docs (cached after first call)
```

### Tool 2: `validate_workflow`

```
INPUT:
  {
    "workflow": object (required)    — Full n8n workflow JSON
  }

OUTPUT:
  {
    "valid": boolean,
    "errors": string[],              — Validation error messages
    "warnings": string[]             — Validation warnings (currently empty)
  }

SIDE EFFECTS: None (pure function)
```

### Tool 3: `deploy_workflow`

```
INPUT:
  {
    "workflow": object (required)    — Full n8n workflow JSON
    "activate": boolean              — Activate after deploy (default: false)
  }

OUTPUT (success):
  {
    "message": "Workflow deployed successfully",
    "workflow": object               — Created workflow (with id assigned)
  }

OUTPUT (error — validation):
  {
    "error": "Validation failed: ...",
    "details": string[]
  }

OUTPUT (error — API):
  {
    "error": "Failed to deploy: 401 Unauthorized"
  }

SIDE EFFECTS:
  - POST /api/v1/workflows (creates workflow)
  - POST /api/v1/workflows/{id}/activate (if activate=true)
```

### Tool 4: `search_nodes`

```
INPUT:
  {
    "query": string (required)       — Search terms
    "limit": number                  — Max results (default: 20)
    "mode": "OR" | "AND" | "FUZZY"  — Search mode (default: "OR")
    "source": "all" | "core" | "community" | "verified"  — Filter (default: "all")
    "includeExamples": boolean       — Include example configs (default: false)
  }

OUTPUT:
  {
    "results": [
      {
        "nodeType": string,
        "displayName": string,
        "description": string,
        "category": string,
        "isTrigger": boolean,
        "isWebhook": boolean,
        "isAITool": boolean
      }
    ],
    "count": number
  }

SIDE EFFECTS: None (read-only SQLite query)
```

### Tool 5: `get_node`

```
INPUT:
  {
    "nodeType": string (required)    — e.g., "nodes-base.httpRequest"
    "detail": "minimal" | "standard" | "full"  — Detail level (default: "standard")
    "mode": "info" | "docs" | "search_properties" | "versions" | "compare" |
            "breaking" | "migrations"   — Operation mode (default: "info")
    "includeTypeInfo": boolean       — Include type metadata (default: false)
    "propertyQuery": string          — Property search (for mode=search_properties)
  }

OUTPUT:
  {
    "nodeType": string,
    "displayName": string,
    "description": string,
    "properties": object,            — Full property schema (if standard/full)
    "operations": array,             — Available operations (if standard/full)
    "documentation": string          — Markdown docs (if available)
  }

SIDE EFFECTS: None
```

### Tool 6: `validate_node`

```
INPUT:
  {
    "nodeType": string (required)    — e.g., "nodes-base.slack"
    "config": object (required)      — Node configuration to validate
    "mode": "minimal" | "full"       — Validation depth (default: "full")
    "profile": "minimal" | "runtime" | "ai-friendly" | "strict"  (default: "runtime")
  }

OUTPUT:
  {
    "valid": boolean,
    "errors": string[],
    "warnings": string[],
    "suggestions": string[]
  }

SIDE EFFECTS: None
```

### Tool 7: `n8n_get_workflow`

```
INPUT:
  {
    "id": string (required)          — Workflow ID
    "mode": "full" | "details" | "structure" | "minimal"  (default: "full")
  }

OUTPUT (mode=full):     Complete workflow JSON
OUTPUT (mode=details):  Workflow + execution stats
OUTPUT (mode=structure): nodes[] + connections{} only
OUTPUT (mode=minimal):  {id, name, active, tags}

SIDE EFFECTS: None (GET request)
```

### Tool 8: `n8n_list_workflows`

```
INPUT:
  {
    "limit": number                  — Max results (optional)
    "cursor": string                 — Pagination cursor (optional)
  }

OUTPUT:
  {
    "data": [workflow objects],
    "nextCursor": string | null
  }

SIDE EFFECTS: None (GET request)
```

### Tool 9: `n8n_update_full_workflow`

```
INPUT:
  {
    "id": string (required)          — Workflow ID to update
    "name": string                   — New name (optional)
    "nodes": array                   — Complete node array (optional)
    "connections": object            — Complete connections (optional)
    "settings": object               — Settings to update (optional)
  }

OUTPUT: Updated workflow JSON

SIDE EFFECTS:
  - Validates workflow structure
  - Cleans fields via clean_workflow_for_update()
  - PUT /api/v1/workflows/{id} (or PATCH fallback)
```

### Tool 10: `n8n_delete_workflow`

```
INPUT:
  { "id": string (required) }

OUTPUT:
  { "success": true, "message": "Workflow deleted" }

SIDE EFFECTS:
  - DELETE /api/v1/workflows/{id}
```

### Tool 11: `n8n_health_check`

```
INPUT:  {} (no parameters)

OUTPUT:
  {
    "status": "ok" | "error",
    "n8nVersion": string | null,
    "features": object
  }

SIDE EFFECTS:
  - GET /healthz (primary)
  - GET /workflows?limit=1 (fallback)
```

### Tool 12: `tools_documentation`

```
INPUT:
  {
    "topic": string                  — Tool name or "overview" (optional)
    "depth": "essentials" | "full"   — Detail level (default: "essentials")
  }

OUTPUT: Markdown documentation string

SIDE EFFECTS: None
```

---

## 2.5 Error Handling Flows

### Error Code Map

```
Domain Exception              →    MCP Code     →    HTTP Analogy
─────────────────────────────────────────────────────────────────
ValidationError               →    MCP-008      →    400 Bad Request
ResourceNotFoundError         →    MCP-005      →    404 Not Found
UnauthorizedError             →    MCP-006      →    401 Unauthorized
RateLimitError                →    MCP-007      →    429 Too Many Requests
ConfigurationError            →    MCP-009      →    500 (misconfigured)
IntegrationError              →    MCP-010      →    502 Bad Gateway
N8nAPIError                   →    MCP-010      →    502 Bad Gateway
ValueError                    →    MCP-002      →    400 Bad Request
KeyError                      →    MCP-002      →    400 Bad Request
(any other Exception)         →    MCP-004      →    500 Internal Error
```

### Error Propagation Path

```
n8n API returns HTTP error
    │
    ▼
N8nApiClient catches httpx.HTTPStatusError
    │
    ├── Wraps in N8nApiError(status_code=401, response={...})
    │
    ▼
N8nWorkflowRepository catches exception
    │
    ├── 404 → Wraps in ResourceNotFoundError
    ├── Other → Re-raises N8nApiError
    │
    ▼
WorkflowGenerationService
    │
    ├── Lets exception propagate (no catch-all)
    │
    ▼
Tool Handler (workflow_tools.py, etc.)
    │
    ├── try/except around handler logic
    ├── Catches known exceptions → returns error JSON string
    ├── Unknown exceptions → re-raises
    │
    ▼
MCP call_tool handler (__main__.py)
    │
    ├── try/except wraps handler execution
    ├── Success → TextContent(text=result, isError=false)
    ├── Exception → MCPErrorHandler.handle_error(error, tool_name)
    │               → MCPResponseFormatter.format_error(code, message)
    │               → TextContent(text=error_json, isError=true)
    │
    ▼
Cursor IDE receives JSON-RPC response
    │
    ├── isError=false → LLM processes result
    ├── isError=true  → LLM shows error to user
```

### Graceful Degradation Matrix

```
┌────────────────────────┬───────────────────────────────────────────────────┐
│ Failure Condition       │ System Behavior                                   │
├────────────────────────┼───────────────────────────────────────────────────┤
│ n8n API unreachable    │ search_nodes ✓  get_node ✓  validate_* ✓         │
│                        │ generate_workflow ✓ (context only, no deploy)     │
│                        │ deploy_workflow ✗  n8n_* tools ✗                  │
│                        │ tools_documentation ✓                             │
├────────────────────────┼───────────────────────────────────────────────────┤
│ nodes.db missing       │ search_nodes ✗  get_node ✗  validate_node ✗      │
│                        │ generate_workflow ✓  deploy_workflow ✓            │
│                        │ validate_workflow ✓  n8n_* tools ✓               │
│                        │ tools_documentation ✓                             │
├────────────────────────┼───────────────────────────────────────────────────┤
│ Both unavailable       │ generate_workflow ✓ (degraded, no node awareness)│
│                        │ validate_workflow ✓ (structural only)            │
│                        │ tools_documentation ✓                             │
│                        │ Everything else ✗                                 │
├────────────────────────┼───────────────────────────────────────────────────┤
│ N8N_API_KEY wrong      │ All n8n_* tools → MCP-006 Unauthorized           │
│                        │ deploy_workflow → MCP-006 Unauthorized            │
│                        │ All local tools ✓                                 │
├────────────────────────┼───────────────────────────────────────────────────┤
│ OpenAPI docs 404       │ generate_workflow ✓ (without API docs context)    │
│                        │ All other tools unaffected                        │
└────────────────────────┴───────────────────────────────────────────────────┘
```

---

## 2.6 Storage Schemas

### SQLite Database: `nodes.db`

**Table: `nodes`**

```sql
CREATE TABLE nodes (
    node_type       TEXT PRIMARY KEY,    -- "n8n-nodes-base.httpRequest"
    display_name    TEXT NOT NULL,       -- "HTTP Request"
    description     TEXT,                -- Human-readable description
    category        TEXT,                -- "Network", "Data", "Communication", etc.
    package_name    TEXT,                -- "n8n-nodes-base"
    properties_schema TEXT,              -- JSON blob: full property definitions
    operations      TEXT,                -- JSON blob: available operations
    documentation   TEXT,                -- Markdown documentation
    version         INTEGER,             -- Node schema version
    is_community    INTEGER DEFAULT 0,   -- 0=core, 1=community
    is_verified     INTEGER DEFAULT 0,   -- 0=no, 1=verified community node
    author_name     TEXT,                -- Package author
    npm_downloads   INTEGER,             -- Download count
    is_trigger      INTEGER DEFAULT 0,   -- 0=no, 1=trigger node
    is_webhook      INTEGER DEFAULT 0,   -- 0=no, 1=webhook trigger
    is_ai_tool      INTEGER DEFAULT 0    -- 0=no, 1=AI/LangChain node
);
```

**Virtual Table: `nodes_fts`**

```sql
CREATE VIRTUAL TABLE nodes_fts USING fts5(
    node_type,
    display_name,
    description,
    category,
    operations,
    content='nodes',
    content_rowid='rowid'
);
```

**Index characteristics:**
- FTS5 tokenizer: default Unicode61
- Ranking: BM25 (FTS5 default)
- Approximate row count: 1000-1500 nodes

### Environment Configuration: `.env`

```
N8N_API_URL=http://localhost:5678       # n8n instance base URL
N8N_API_KEY=your-api-key-here           # n8n API authentication key
N8N_NODE_DB_PATH=./data/nodes.db        # Path to SQLite node database
LOG_LEVEL=info                          # debug | info | warning | error
CACHE_TTL_SECONDS=3600                  # Cache time-to-live (seconds)
```

### In-Memory State (Runtime Only)

```
ToolRegistry (singleton)
├── _tools: Dict[str, ToolDefinition]    # All registered tools
└── _instance: Optional[ToolRegistry]    # Singleton reference

N8nDocsFetcher
└── _cached_docs: Optional[str]          # Cached OpenAPI docs (in-memory)

NodeRepository
└── _conn: Optional[sqlite3.Connection]  # Singleton DB connection

Logger (singleton)
├── _logger: logging.Logger              # Python logger instance
└── _instance: Optional[Logger]          # Singleton reference

N8nApiClient
└── _client: httpx.AsyncClient           # Persistent HTTP client
```

---

## 2.7 Dependency Graph

### Import Dependency Graph (Actual)

```
                     __main__.py
                    ╱    │     ╲
                   ╱     │      ╲
                  ╱      │       ╲
                 ▼       ▼        ▼
            env.py    tools/*   services/
              │       ╱  │  ╲     │
              │      ╱   │   ╲    │
              ▼     ▼    ▼    ▼   ▼
           n8n_config  node_  n8n/repositories/
              │       repo     │
              │        │       │
              ▼        │       ▼
         n8n_api_client│   n8n_validator
              │        │       │
              ▼        ▼       ▼
           logger/logger.py
              │
              ▼
         domain/types.py ◄─── domain/errors.py
              │
              ▼
          (stdlib only)
```

### External Dependency Graph

```
n8n-workflow-generator-mcp
├── mcp (SDK)                   # MCP protocol, Server, stdio_server
│   └── anyio                   # Async I/O abstraction
├── pydantic >= 2.0             # Data validation
│   └── pydantic-core           # Rust-based validation core
├── httpx                       # Async HTTP client
│   ├── httpcore                # HTTP/1.1 & HTTP/2
│   └── anyio                   # (shared with mcp)
├── python-dotenv               # .env file loading
└── stdlib
    ├── asyncio                 # Event loop
    ├── sqlite3                 # Database access
    ├── json                    # Serialization
    ├── logging                 # Logging framework
    ├── sys                     # System access
    ├── os                      # Environment vars
    ├── pathlib                 # File paths
    ├── dataclasses             # Domain models
    ├── typing                  # Type hints
    ├── enum                    # Enumerations
    └── abc                     # Abstract base classes
```

### Runtime Object Graph (on startup)

```
N8nWorkflowGeneratorServer
├── server: mcp.server.Server
│   ├── list_tools handler (closure)
│   └── call_tool handler (closure)
│
├── tool_registry: ToolRegistry (singleton)
│   └── _tools: {
│       "generate_workflow":      ToolDefinition → handler closure
│       "validate_workflow":      ToolDefinition → handler closure
│       "deploy_workflow":        ToolDefinition → handler closure
│       "search_nodes":           ToolDefinition → handler closure
│       "get_node":               ToolDefinition → handler closure
│       "validate_node":          ToolDefinition → handler closure
│       "n8n_get_workflow":       ToolDefinition → handler closure
│       "n8n_list_workflows":     ToolDefinition → handler closure
│       "n8n_update_full_workflow": ToolDefinition → handler closure
│       "n8n_delete_workflow":    ToolDefinition → handler closure
│       "n8n_health_check":       ToolDefinition → handler closure
│       "tools_documentation":    ToolDefinition → handler closure
│   }
│
├── api_client: N8nApiClient (if configured)
│   └── _client: httpx.AsyncClient
│       ├── base_url: "http://localhost:5678/api/v1"
│       ├── headers: {"X-N8N-API-KEY": "...", "Content-Type": "..."}
│       └── timeout: httpx.Timeout(30.0)
│
├── workflow_repository: N8nWorkflowRepository (if api_client exists)
│   └── _api_client: → api_client (shared reference)
│
├── service: WorkflowGenerationService (if repository exists)
│   └── workflow_repository: → workflow_repository (shared reference)
│
├── node_repository: NodeRepository (if DB path exists)
│   ├── db_path: "/path/to/nodes.db"
│   └── _conn: sqlite3.Connection (lazy, created on first query)
│
└── logger: Logger (singleton, shared across all components)
    └── _logger: logging.Logger("n8n-workflow-generator")
        └── handler: StreamHandler(sys.stderr)
```

---

## 2.8 Infrastructure Topology

### Current: Local Development

```
┌─────────────────────────────────────────────────────────┐
│                   DEVELOPER MACHINE                      │
│                                                          │
│  ┌─────────────────┐     ┌──────────────────────────┐   │
│  │   Cursor IDE     │     │  n8n (Docker or native)  │   │
│  │                  │     │                          │   │
│  │  ┌────────────┐  │     │  Port 5678               │   │
│  │  │ MCP Client │  │     │  ┌──────────────────┐    │   │
│  │  └─────┬──────┘  │     │  │  REST API v1     │    │   │
│  │        │ stdio   │     │  │  /api/v1/*       │    │   │
│  │        │         │     │  └──────────────────┘    │   │
│  └────────┼─────────┘     └──────────┬───────────────┘   │
│           │                          │                    │
│           ▼                          │                    │
│  ┌─────────────────┐                 │                    │
│  │ MCP Server      │   HTTP/REST     │                    │
│  │ (python process) ├────────────────┘                    │
│  │                  │                                     │
│  │ ┌──────────────┐│                                     │
│  │ │  nodes.db    ││                                     │
│  │ │  (SQLite)    ││                                     │
│  │ └──────────────┘│                                     │
│  └─────────────────┘                                     │
│                                                          │
│  Filesystem:                                             │
│  ├── .env (N8N_API_URL, N8N_API_KEY)                    │
│  ├── data/nodes.db                                      │
│  └── src/ (Python source)                               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Target: Dockerized Distribution (Phase 5)

```
┌─────────────────────────────────────────────────────────────────┐
│                      DEVELOPER MACHINE                           │
│                                                                   │
│  ┌─────────────────┐                                             │
│  │   Cursor IDE     │                                             │
│  │  ┌────────────┐  │                                             │
│  │  │ MCP Client │  │                                             │
│  │  └─────┬──────┘  │                                             │
│  └────────┼─────────┘                                             │
│           │ stdio                                                 │
│           ▼                                                       │
│  ┌──────────────────────────── docker-compose ────────────────┐   │
│  │                                                             │   │
│  │  ┌──────────────────────┐    ┌──────────────────────────┐  │   │
│  │  │ flowforge-mcp        │    │ n8n                       │  │   │
│  │  │ (Python container)   │    │ (n8n container)           │  │   │
│  │  │                      │    │                           │  │   │
│  │  │ Port: stdio (host)   │    │ Port: 5678:5678          │  │   │
│  │  │                      │    │                           │  │   │
│  │  │ Volumes:             │    │ Volumes:                  │  │   │
│  │  │ - ./data:/app/data   │    │ - n8n_data:/home/node     │  │   │
│  │  │ - ./.env:/app/.env   │    │                           │  │   │
│  │  │                      │    │                           │  │   │
│  │  │ Network:             │    │ Network:                  │  │   │
│  │  │ flowforge_net ───────┼────┤ flowforge_net             │  │   │
│  │  │                      │    │                           │  │   │
│  │  └──────────────────────┘    └──────────────────────────┘  │   │
│  │                                                             │   │
│  │  Volumes:                                                   │   │
│  │  - n8n_data (persistent)                                    │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2.9 Concurrency Model

### Current: Single-Threaded Async

```
┌─────────────────────────────────────────────────────────┐
│              Python asyncio Event Loop                    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Main coroutine: server.run()                      │   │
│  │                                                    │   │
│  │  ┌─── stdio_server context manager ────────────┐  │   │
│  │  │                                              │  │   │
│  │  │  stdin reader ──► JSON-RPC parser            │  │   │
│  │  │       │                                      │  │   │
│  │  │       ▼                                      │  │   │
│  │  │  call_tool handler (async)                   │  │   │
│  │  │       │                                      │  │   │
│  │  │       ├── await tool_handler()               │  │   │
│  │  │       │       │                              │  │   │
│  │  │       │       ├── await httpx request        │  │   │
│  │  │       │       │   (yields to event loop)     │  │   │
│  │  │       │       │                              │  │   │
│  │  │       │       ├── sqlite3 query              │  │   │
│  │  │       │       │   (BLOCKING — not async)     │  │   │
│  │  │       │       │                              │  │   │
│  │  │       │       └── return result              │  │   │
│  │  │       │                                      │  │   │
│  │  │       └── write TextContent to stdout        │  │   │
│  │  │                                              │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  IMPORTANT: SQLite calls are synchronous (blocking).         │
│  This is fine for single-user but would block the event      │
│  loop under concurrent load. Future fix: run_in_executor().  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Concurrency Risks

| Operation | Blocking? | Risk Level | Mitigation |
|-----------|-----------|------------|------------|
| httpx HTTP requests | No (async) | None | Properly awaited |
| SQLite queries | **Yes (sync)** | Low (single-user) | Could use `run_in_executor()` |
| JSON serialization | Yes (sync, fast) | None | < 1ms typically |
| Pydantic validation | Yes (sync, fast) | None | < 10ms typically |
| File I/O (.env) | Yes (sync, startup only) | None | Only at initialization |

---

## 2.10 Security Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│ TRUST BOUNDARY 1: Process Boundary                           │
│                                                               │
│ Cursor IDE (trusted) ──stdio──► MCP Server (trusted)         │
│                                                               │
│ No authentication. Cursor spawns the process.                 │
│ Whoever has access to Cursor has access to all tools.         │
│ This is acceptable for single-user local deployment.          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ TRUST BOUNDARY 2: Network Boundary                           │
│                                                               │
│ MCP Server ──HTTP──► n8n Instance                            │
│                                                               │
│ Authenticated via X-N8N-API-KEY header.                      │
│ API key stored in .env file (plaintext).                     │
│ All requests over HTTP (not HTTPS by default for localhost). │
│                                                               │
│ RISKS:                                                        │
│ - API key in plaintext on disk                               │
│ - No key rotation mechanism                                  │
│ - HTTP (not HTTPS) for localhost — fine locally, not remotely │
│ - No request signing or mutual TLS                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ TRUST BOUNDARY 3: Data Boundary                              │
│                                                               │
│ nodes.db is READ-ONLY from the server's perspective.         │
│ No user data is persisted by the MCP server.                 │
│ Workflow data flows through to n8n but is not stored locally.│
│                                                               │
│ What IS logged (stderr):                                      │
│ - Tool invocations and arguments                             │
│ - Error messages and stack traces                            │
│ - Workflow names (not full workflow content)                  │
│                                                               │
│ What is NOT logged:                                           │
│ - API keys                                                   │
│ - Full workflow JSON                                         │
│ - Credential references                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 2.11 Performance Characteristics

### Latency Budget (per operation)

```
generate_workflow (total: ~1-3s)
├── N8nDocsFetcher.fetch_docs()     ~500ms-2s  (network, cached after first)
├── Format context string           ~1-5ms     (string operations)
└── Return to Cursor                ~1ms       (stdio write)

validate_workflow (total: ~50-100ms)
├── validate_workflow_structure()   ~30-60ms   (Pydantic + rule checks)
└── JSON serialization              ~5-20ms    (json.dumps)

deploy_workflow (total: ~500ms-2s)
├── validate_workflow_structure()   ~50ms
├── clean_workflow_for_create()     ~5ms
├── POST /api/v1/workflows          ~300ms-1.5s (network)
└── POST .../activate (optional)    ~200ms-500ms (network)

search_nodes (total: ~5-30ms)
├── FTS5 MATCH query                ~2-10ms
├── _row_to_dict × N results        ~3-15ms
└── JSON serialization              ~1-5ms

get_node (total: ~3-15ms)
├── SELECT WHERE node_type = ?      ~1-5ms
├── _row_to_dict                    ~1-5ms
└── JSON serialization              ~1-5ms
```

### Memory Footprint

```
Component                          Approximate Size
──────────────────────────────────────────────────
Python runtime                     ~30-50 MB
MCP SDK + server                   ~5-10 MB
httpx client (connection pool)     ~2-5 MB
SQLite connection + FTS5 index     ~5-20 MB (depends on DB size)
Cached OpenAPI docs                ~100-500 KB
Tool registry (12 tools)           ~10 KB
Logger                             ~1 KB
──────────────────────────────────────────────────
Total estimated                    ~50-90 MB
```

---

*End of System Design Document*

"""Domain types for n8n workflow generator."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Protocol


# Domain entities
@dataclass
class WorkflowNode:
    """Represents an n8n workflow node."""
    id: str
    name: str
    type: str  # Full form: "n8n-nodes-base.httpRequest"
    typeVersion: int
    position: List[int]  # [x, y] coordinates
    parameters: Dict[str, Any]
    credentials: Optional[Dict[str, Any]] = None
    disabled: bool = False
    notes: Optional[str] = None
    continueOnFail: bool = False
    retryOnFail: bool = False
    maxTries: Optional[int] = None
    waitBetweenTries: Optional[int] = None


@dataclass
class Workflow:
    """Represents a complete n8n workflow."""
    id: Optional[str] = None
    name: str = ""
    nodes: List[WorkflowNode] = None
    connections: Dict[str, Any] = None
    settings: Optional[Dict[str, Any]] = None
    active: bool = False
    tags: Optional[List[str]] = None

    def __post_init__(self):
        if self.nodes is None:
            self.nodes = []
        if self.connections is None:
            self.connections = {}


# Repository Protocols (interfaces)
class WorkflowRepository(Protocol):
    """Protocol for workflow repository."""
    
    async def create(self, workflow: Workflow) -> Workflow:
        """Create a new workflow."""
        ...
    
    async def find_by_id(self, workflow_id: str) -> Optional[Workflow]:
        """Find workflow by ID."""
        ...
    
    async def update(self, workflow_id: str, workflow: Workflow) -> Workflow:
        """Update existing workflow."""
        ...
    
    async def delete(self, workflow_id: str) -> None:
        """Delete workflow."""
        ...
    
    async def list(self, **filters) -> List[Workflow]:
        """List workflows with optional filters."""
        ...


# Type aliases
WorkflowId = str
NodeId = str



"""Environment configuration."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class Config:
    """Application configuration."""
    
    # n8n API Configuration
    n8n_api_url: Optional[str] = None
    n8n_api_key: Optional[str] = None
    
    # Node Database Configuration
    n8n_node_db_path: Optional[str] = None
    
    # Logging
    log_level: str = "info"
    
    # Cache
    cache_ttl_seconds: int = 3600
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        # Default node DB path (relative to project root, pointing to n8n-mcp database)
        default_node_db = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "n8n-mcp",
            "data",
            "nodes.db"
        )
        
        return cls(
            n8n_api_url=os.getenv("N8N_API_URL"),
            n8n_api_key=os.getenv("N8N_API_KEY"),
            n8n_node_db_path=os.getenv("N8N_NODE_DB_PATH", default_node_db),
            log_level=os.getenv("LOG_LEVEL", "info"),
            cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "3600")),
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        # n8n API is optional (only needed for deployment)
        # No validation errors if not set


# Global configuration instance
config = Config.from_env()



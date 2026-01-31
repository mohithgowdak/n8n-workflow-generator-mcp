"""n8n API configuration."""

from dataclasses import dataclass
from typing import Optional
from ...env import config


@dataclass
class N8nConfig:
    """n8n API configuration."""
    
    base_url: str
    api_key: str
    timeout: int = 30
    max_retries: int = 3
    
    @classmethod
    def from_env(cls) -> Optional["N8nConfig"]:
        """Load configuration from environment."""
        if not config.n8n_api_url or not config.n8n_api_key:
            return None
        
        # Ensure base_url ends with /api/v1
        base_url = config.n8n_api_url
        if not base_url.endswith('/api/v1'):
            base_url = f"{base_url.rstrip('/')}/api/v1"
        
        return cls(
            base_url=base_url,
            api_key=config.n8n_api_key,
            timeout=30,
            max_retries=3
        )
    
    def validate(self) -> None:
        """Validate configuration."""
        if not self.base_url:
            raise ValueError("n8n base_url is required")
        if not self.api_key:
            raise ValueError("n8n api_key is required")
    
    def is_configured(self) -> bool:
        """Check if n8n API is configured."""
        return bool(self.base_url and self.api_key)



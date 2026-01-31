"""Base repository for n8n operations."""

from typing import Protocol, Optional
from abc import ABC, abstractmethod
from ..util.n8n_api_client import N8nApiClient
from ...logger.logger import Logger


class IN8nRepository(Protocol):
    """n8n repository interface."""
    
    @property
    def api_client(self) -> N8nApiClient:
        """Get API client."""
        ...


class BaseN8nRepository(ABC):
    """Base repository for n8n operations."""
    
    def __init__(self, api_client: N8nApiClient):
        """Initialize base repository."""
        self._api_client = api_client
        self._logger = Logger.get_instance()
    
    @property
    def api_client(self) -> N8nApiClient:
        """Get API client."""
        return self._api_client


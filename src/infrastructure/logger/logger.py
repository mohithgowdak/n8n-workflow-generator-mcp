"""Logging infrastructure."""

import logging
import sys
from typing import Optional


class Logger:
    """Centralized logger."""
    
    _instance: Optional["Logger"] = None
    
    def __init__(self):
        """Initialize logger."""
        self.logger = logging.getLogger("n8n-workflow-generator")
        self.logger.setLevel(logging.INFO)
        
        # Console handler
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    @classmethod
    def get_instance(cls) -> "Logger":
        """Get singleton logger instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message."""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message."""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message."""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message."""
        self.logger.error(message, *args, **kwargs)
    
    def set_level(self, level: str):
        """Set log level."""
        level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
        }
        self.logger.setLevel(level_map.get(level.lower(), logging.INFO))


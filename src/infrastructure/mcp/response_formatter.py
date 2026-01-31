"""MCP response formatting utilities."""

import json
from typing import Any, Dict, Optional, List
from enum import Enum


class MCPContentType(str, Enum):
    """MCP content types."""
    TEXT = "text/plain"
    JSON = "application/json"
    MARKDOWN = "text/markdown"
    HTML = "text/html"


class MCPResponseFormatter:
    """Formatter for MCP responses."""
    
    @staticmethod
    def format_text(text: str) -> str:
        """Format as plain text."""
        return text
    
    @staticmethod
    def format_json(data: Any, indent: int = 2) -> str:
        """Format as JSON."""
        return json.dumps(data, indent=indent, default=str)
    
    @staticmethod
    def format_markdown(data: Any) -> str:
        """Format as markdown."""
        if isinstance(data, dict):
            return MCPResponseFormatter._dict_to_markdown(data)
        elif isinstance(data, list):
            return MCPResponseFormatter._list_to_markdown(data)
        else:
            return str(data)
    
    @staticmethod
    def format_html(data: Any) -> str:
        """Format as HTML."""
        if isinstance(data, dict):
            return MCPResponseFormatter._dict_to_html(data)
        elif isinstance(data, list):
            return MCPResponseFormatter._list_to_html(data)
        else:
            return f"<p>{str(data)}</p>"
    
    @staticmethod
    def format_success(
        data: Any,
        content_type: MCPContentType = MCPContentType.JSON,
        message: Optional[str] = None
    ) -> str:
        """Format a success response."""
        result = {}
        
        if message:
            result["message"] = message
        
        if content_type == MCPContentType.JSON:
            result["data"] = data
            return MCPResponseFormatter.format_json(result)
        elif content_type == MCPContentType.MARKDOWN:
            if message:
                result["message"] = message
            result["data"] = data
            return MCPResponseFormatter.format_markdown(result)
        elif content_type == MCPContentType.HTML:
            result["data"] = data
            return MCPResponseFormatter.format_html(result)
        else:
            if message:
                return f"{message}\n\n{str(data)}"
            return str(data)
    
    @staticmethod
    def format_error(
        error_code: str,
        error_message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format an error response."""
        error = {
            "error": {
                "code": error_code,
                "message": error_message
            }
        }
        
        if details:
            error["error"]["details"] = details
        
        return MCPResponseFormatter.format_json(error)
    
    @staticmethod
    def _dict_to_markdown(data: Dict[str, Any], level: int = 1) -> str:
        """Convert dictionary to markdown."""
        lines = []
        for key, value in data.items():
            header = "#" * level
            formatted_key = key.replace("_", " ").title()
            
            if isinstance(value, dict):
                lines.append(f"{header} {formatted_key}")
                lines.append(MCPResponseFormatter._dict_to_markdown(value, level + 1))
            elif isinstance(value, list):
                lines.append(f"{header} {formatted_key}")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(MCPResponseFormatter._dict_to_markdown(item, level + 1))
                    else:
                        lines.append(f"- {item}")
            else:
                lines.append(f"**{formatted_key}**: {value}")
        
        return "\n\n".join(lines)
    
    @staticmethod
    def _list_to_markdown(data: List[Any]) -> str:
        """Convert list to markdown."""
        lines = []
        for item in data:
            if isinstance(item, dict):
                lines.append(MCPResponseFormatter._dict_to_markdown(item))
            else:
                lines.append(f"- {item}")
        return "\n".join(lines)
    
    @staticmethod
    def _dict_to_html(data: Dict[str, Any]) -> str:
        """Convert dictionary to HTML."""
        html = "<div>"
        for key, value in data.items():
            formatted_key = key.replace("_", " ").title()
            html += f"<h3>{formatted_key}</h3>"
            if isinstance(value, (dict, list)):
                html += f"<pre>{json.dumps(value, indent=2)}</pre>"
            else:
                html += f"<p>{value}</p>"
        html += "</div>"
        return html
    
    @staticmethod
    def _list_to_html(data: List[Any]) -> str:
        """Convert list to HTML."""
        html = "<ul>"
        for item in data:
            if isinstance(item, dict):
                html += f"<li><pre>{json.dumps(item, indent=2)}</pre></li>"
            else:
                html += f"<li>{item}</li>"
        html += "</ul>"
        return html
    
    @staticmethod
    def format_table(data: List[Dict[str, Any]], title: Optional[str] = None) -> str:
        """Format data as a markdown table."""
        if not data:
            return ""
        
        # Get all keys from all items
        keys = set()
        for item in data:
            keys.update(item.keys())
        keys = sorted(keys)
        
        lines = []
        if title:
            lines.append(f"## {title}\n")
        
        # Create table header
        header = "| " + " | ".join(keys) + " |"
        separator = "| " + " | ".join(["---"] * len(keys)) + " |"
        lines.append(header)
        lines.append(separator)
        
        # Create table rows
        for item in data:
            row = "| " + " | ".join(str(item.get(key, "")) for key in keys) + " |"
            lines.append(row)
        
        return "\n".join(lines)


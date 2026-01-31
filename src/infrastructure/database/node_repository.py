"""Repository for querying n8n node database."""

import sqlite3
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from ...infrastructure.logger.logger import Logger


class NodeRepository:
    """Repository for querying n8n nodes from SQLite database."""
    
    def __init__(self, db_path: str):
        """Initialize repository with database path."""
        self.db_path = db_path
        self.logger = Logger.get_instance()
        self._conn: Optional[sqlite3.Connection] = None
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._conn is None:
            if not Path(self.db_path).exists():
                raise FileNotFoundError(f"Database file not found: {self.db_path}")
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row  # Enable column access by name
        return self._conn
    
    def close(self):
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def search_nodes(
        self,
        query: str,
        limit: int = 20,
        mode: str = 'OR',
        source: str = 'all',
        include_examples: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search nodes using FTS5 full-text search or LIKE fallback.
        
        Args:
            query: Search query string
            limit: Maximum results to return
            mode: Search mode ('OR', 'AND', 'FUZZY')
            source: Filter by source ('all', 'core', 'community', 'verified')
            include_examples: Whether to include example configurations
        
        Returns:
            List of node dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check if FTS5 table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='nodes_fts'
        """)
        fts_exists = cursor.fetchone() is not None
        
        if fts_exists:
            return self._search_nodes_fts(cursor, query, limit, mode, source, include_examples)
        else:
            return self._search_nodes_like(cursor, query, limit, source, include_examples)
    
    def _search_nodes_fts(
        self,
        cursor: sqlite3.Cursor,
        query: str,
        limit: int,
        mode: str,
        source: str,
        include_examples: bool
    ) -> List[Dict[str, Any]]:
        """Search using FTS5 full-text search."""
        # Normalize query
        normalized_query = query.replace('n8n-nodes-base.', 'nodes-base.')
        normalized_query = normalized_query.replace('@n8n/n8n-nodes-langchain.', 'nodes-langchain.')
        
        # Build FTS query based on mode
        if mode == 'AND':
            fts_query = ' AND '.join(f'"{word}"' for word in normalized_query.split())
        elif mode == 'FUZZY':
            # Fuzzy search with wildcards
            fts_query = ' OR '.join(f'{word}*' for word in normalized_query.split())
        else:  # OR mode (default)
            fts_query = normalized_query
        
        # Build source filter
        source_filter = ""
        if source == 'core':
            source_filter = "AND (is_community = 0 OR is_community IS NULL)"
        elif source == 'community':
            source_filter = "AND is_community = 1"
        elif source == 'verified':
            source_filter = "AND is_community = 1 AND is_verified = 1"
        
        # Query with FTS5
        sql = f"""
            SELECT 
                n.*,
                rank
            FROM nodes_fts
            JOIN nodes n ON nodes_fts.rowid = n.rowid
            WHERE nodes_fts MATCH ?
            {source_filter}
            ORDER BY rank
            LIMIT ?
        """
        
        cursor.execute(sql, (fts_query, limit))
        rows = cursor.fetchall()
        
        return [self._row_to_dict(row, include_examples) for row in rows]
    
    def _search_nodes_like(
        self,
        cursor: sqlite3.Cursor,
        query: str,
        limit: int,
        source: str,
        include_examples: bool
    ) -> List[Dict[str, Any]]:
        """Fallback to LIKE search if FTS5 not available."""
        # Normalize query
        normalized_query = query.replace('n8n-nodes-base.', 'nodes-base.')
        normalized_query = normalized_query.replace('@n8n/n8n-nodes-langchain.', 'nodes-langchain.')
        
        # Build source filter
        source_filter = ""
        if source == 'core':
            source_filter = "AND (is_community = 0 OR is_community IS NULL)"
        elif source == 'community':
            source_filter = "AND is_community = 1"
        elif source == 'verified':
            source_filter = "AND is_community = 1 AND is_verified = 1"
        
        # LIKE search
        search_pattern = f"%{normalized_query}%"
        sql = f"""
            SELECT * FROM nodes
            WHERE (
                display_name LIKE ? OR
                description LIKE ? OR
                node_type LIKE ?
            )
            {source_filter}
            ORDER BY display_name
            LIMIT ?
        """
        
        cursor.execute(sql, (search_pattern, search_pattern, search_pattern, limit))
        rows = cursor.fetchall()
        
        return [self._row_to_dict(row, include_examples) for row in rows]
    
    def get_node(
        self,
        node_type: str,
        detail: str = 'standard',
        mode: str = 'info'
    ) -> Optional[Dict[str, Any]]:
        """
        Get node information by node type.
        
        Args:
            node_type: Full node type (e.g., 'nodes-base.httpRequest')
            detail: Detail level ('minimal', 'standard', 'full')
            mode: Operation mode ('info', 'docs', etc.)
        
        Returns:
            Node dictionary or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Normalize node type
        normalized_type = node_type.replace('n8n-nodes-base.', 'nodes-base.')
        normalized_type = normalized_type.replace('@n8n/n8n-nodes-langchain.', 'nodes-langchain.')
        
        # Try normalized first
        cursor.execute("SELECT * FROM nodes WHERE node_type = ?", (normalized_type,))
        row = cursor.fetchone()
        
        # Fallback to original if not found
        if not row and normalized_type != node_type:
            cursor.execute("SELECT * FROM nodes WHERE node_type = ?", (node_type,))
            row = cursor.fetchone()
        
        if not row:
            return None
        
        return self._row_to_dict(row, include_examples=False, detail=detail, mode=mode)
    
    def _row_to_dict(
        self,
        row: sqlite3.Row,
        include_examples: bool = False,
        detail: str = 'standard',
        mode: str = 'info'
    ) -> Dict[str, Any]:
        """Convert database row to dictionary."""
        result = {
            'nodeType': row['node_type'],
            'displayName': row['display_name'],
            'description': row['description'] or '',
            'category': row['category'] or '',
            'packageName': row['package_name'],
        }
        
        # Add properties schema if available
        if row['properties_schema']:
            try:
                props = json.loads(row['properties_schema'])
                if detail in ('standard', 'full'):
                    result['properties'] = props
            except json.JSONDecodeError:
                pass
        
        # Add operations if available
        if row['operations'] and detail in ('standard', 'full'):
            try:
                result['operations'] = json.loads(row['operations'])
            except json.JSONDecodeError:
                pass
        
        # Add documentation if available
        if row['documentation']:
            result['documentation'] = row['documentation']
        
        # Add community node fields if present
        # Use try/except since sqlite3.Row doesn't have .get() method
        try:
            if 'is_community' in row.keys() and row['is_community']:
                result['isCommunity'] = True
                if 'is_verified' in row.keys() and row['is_verified']:
                    result['isVerified'] = True
                if 'author_name' in row.keys() and row['author_name']:
                    result['authorName'] = row['author_name']
                if 'npm_downloads' in row.keys() and row['npm_downloads']:
                    result['npmDownloads'] = row['npm_downloads']
        except (KeyError, IndexError):
            pass
        
        # Add metadata
        result['isTrigger'] = bool(row['is_trigger'] if 'is_trigger' in row.keys() else 0)
        result['isWebhook'] = bool(row['is_webhook'] if 'is_webhook' in row.keys() else 0)
        result['isAITool'] = bool(row['is_ai_tool'] if 'is_ai_tool' in row.keys() else 0)
        
        return result


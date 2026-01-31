#!/usr/bin/env python3
"""Wrapper script to run the MCP server - ensures proper path setup."""

import sys
import os
from pathlib import Path

# Get the project root directory (where this script is located)
_project_root = Path(__file__).parent.resolve()

# Add project root to Python path
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# Change to project root directory
os.chdir(_project_root)

# Now run the module
if __name__ == "__main__":
    from src.__main__ import main
    main()


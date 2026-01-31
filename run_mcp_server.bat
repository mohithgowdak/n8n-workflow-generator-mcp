@echo off
REM Wrapper script to run the MCP server with correct working directory
cd /d "%~dp0"
call venv\Scripts\python.exe -m src

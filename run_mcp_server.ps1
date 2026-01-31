# Wrapper script to run the MCP server with correct working directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath
& "$scriptPath\venv\Scripts\python.exe" -m src

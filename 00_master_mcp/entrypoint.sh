#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Print commands and their arguments as they are executed.
# set -x # Uncomment for debugging

echo "--- Master Orchestrator Entrypoint (Direct FastMCP Run) ---"

# Variables for Uvicorn are no longer directly used by the execution command,
# but we can still display them if they are set for informational purposes.
echo "MCP_PORT (from env, if set): ${MCP_PORT:-8000} (Note: Port is now configured in mcp_host.py for FastMCP run)"
echo "LOG_LEVEL (from env, if set): ${LOG_LEVEL:-info} (Note: Log level is now configured in mcp_host.py for FastMCP run)"

echo "--- Content of mcp_host.py as seen by container: ---"
cat /workspace/mcp_host.py
echo "--- End of mcp_host.py content ---"

echo "Executing Python script: python /workspace/mcp_host.py"

# Execute the python script directly. `exec` replaces the shell process with the Python process.
exec python /workspace/mcp_host.py 
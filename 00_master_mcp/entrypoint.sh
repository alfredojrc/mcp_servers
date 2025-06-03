#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Print commands and their arguments as they are executed.
# set -x # Uncomment for debugging

SERVICE_PORT=${MCP_PORT:-8000}
LOG_LEVEL_CONFIG=${LOG_LEVEL:-info} # Default to info if not set

# Corrected application variable name
APP_VARIABLE_NAME="main_app"

echo "--- Master Orchestrator Entrypoint ---"
echo "MCP_PORT: ${SERVICE_PORT}"
echo "LOG_LEVEL: ${LOG_LEVEL_CONFIG}"
echo "Executing Uvicorn: uvicorn mcp_host:${APP_VARIABLE_NAME} --host 0.0.0.0 --port ${SERVICE_PORT} --log-level ${LOG_LEVEL_CONFIG}"
echo "------------------------------------"

# Execute the Python script directly to run FastMCP with SSE
exec python mcp_host.py 
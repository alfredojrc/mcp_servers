#!/bin/bash
set -e

echo "Starting Aider MCP Server (14_aider_mcp)..."

# Create workspace directory if it doesn't exist
mkdir -p ${REPO_PATH:-/workspace}

# Check if aider is installed
if ! command -v aider &> /dev/null; then
    echo "Aider not found, installing..."
    pip install aider-chat
fi

# Run the MCP server
exec python /app/mcp_server.py
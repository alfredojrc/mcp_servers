#!/bin/bash
set -e

echo "Starting Web Search MCP Server..."
echo "Port: ${MCP_PORT:-8006}"

# Run the MCP server
exec python -u mcp_server.py
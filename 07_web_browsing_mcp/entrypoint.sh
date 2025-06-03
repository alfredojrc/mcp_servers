#!/bin/bash
set -e

echo "Starting Web Browsing MCP Server..."
echo "Port: ${MCP_PORT:-8007}"
echo "Browser: ${BROWSER_TYPE:-chromium}"

# Run the MCP server
exec python -u mcp_server.py
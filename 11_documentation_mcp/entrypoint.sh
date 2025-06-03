#!/bin/bash
set -e

echo "Starting Documentation MCP Server..."
echo "Service: 11_documentation_mcp"
echo "Port: ${MCP_PORT:-8011}"
echo "Docs Root: ${DOCS_ROOT:-/workspace/docs}"
echo "Approval Required: ${REQUIRE_APPROVAL:-true}"

# Ensure directories exist
mkdir -p ${DOCS_ROOT:-/workspace/docs}
mkdir -p /workspace/search_index

# Create category directories
for category in projects services whitepapers guides api knowledge; do
    mkdir -p "${DOCS_ROOT:-/workspace/docs}/$category"
done

# Start the MCP server
exec python mcp_server.py
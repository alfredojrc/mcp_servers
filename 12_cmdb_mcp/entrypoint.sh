#!/usr/bin/env bash
set -euo pipefail

echo "Starting CMDB MCP Server (12_cmdb_mcp)..."

# Execute the main Python server script
exec python -u mcp_server.py 
#!/usr/bin/env bash
set -euo pipefail

echo "Starting Secrets MCP Server (13_secrets_mcp)..."

# Execute the main Python server script
exec python -u mcp_server.py 
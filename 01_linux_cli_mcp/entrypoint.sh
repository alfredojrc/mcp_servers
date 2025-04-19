#!/usr/bin/env bash
set -euo pipefail

# Any setup tasks could go here (e.g., initializing SSH agent if using keys)

echo "Starting Linux CLI MCP Server (01_linux_cli_mcp)..."

# Execute the main Python server script
exec python -u mcp_server.py 
#!/usr/bin/env bash
set -euo pipefail

# Any setup tasks could go here (e.g., waiting for other services)

echo "Starting MCP Host (00_master_mcp)..."

# Execute the main Python host script
# Ensure Python outputs are not buffered, which helps with logging in Docker
exec python -u mcp_host.py 
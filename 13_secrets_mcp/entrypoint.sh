#!/usr/bin/env bash
set -euo pipefail

echo "Starting Secrets MCP Server (13_secrets_mcp) via python mcp_server.py..."

# Debug: Print the KEEPASS_DB_PATH environment variable safely
echo "DEBUG: KEEPASS_DB_PATH is set to: [${KEEPASS_DB_PATH:-NOT_SET_IN_ENTRYPOINT_ENV}]"

# Execute the main Python server script
exec python -u mcp_server.py 
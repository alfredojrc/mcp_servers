#!/bin/bash
set -e

echo "Starting Vector Database MCP Service on port ${MCP_PORT:-8018}..."

# Create necessary directories
mkdir -p /app/data/chroma

# Start the service
exec python mcp_server.py
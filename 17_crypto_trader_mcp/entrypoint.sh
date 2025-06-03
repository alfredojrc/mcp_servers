#!/bin/bash
set -e

echo "Starting Crypto Trader MCP Server..."
echo "Service: 17_crypto_trader_mcp"
echo "Port: ${MCP_PORT:-8017}"
echo "Default Exchange: ${DEFAULT_EXCHANGE:-binance}"
echo "Paper Trading: ${ENABLE_PAPER_TRADING:-true}"

# Ensure data directories exist
mkdir -p /workspace/data/cache
mkdir -p /workspace/data/historical

# Start the MCP server
exec python mcp_server.py
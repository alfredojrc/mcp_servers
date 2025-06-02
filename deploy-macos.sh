#!/bin/bash
# Deploy MCP stack on macOS (laptop)

echo "🚀 Deploying MCP stack for macOS..."

# Use both base and macOS-specific configs
docker-compose -f docker-compose.yml -f docker-compose.macos.yml up -d --build

echo "✅ macOS MCP stack deployed!"
echo "📍 Hub mode - can manage remote servers via SSH"
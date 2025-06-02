#!/bin/bash
# Deploy MCP stack on Ubuntu (aicrusher)

echo "🚀 Deploying MCP stack for Ubuntu..."

# Use both base and Ubuntu-specific configs
docker-compose -f docker-compose.yml -f docker-compose.ubuntu.yml up -d --build

echo "✅ Ubuntu MCP stack deployed!"
echo "📍 Services running locally - no SSH routing needed"
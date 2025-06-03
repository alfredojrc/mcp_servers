# Claude Code Global Setup Guide

This guide helps you configure Claude Code to access all MCP services from any project directory.

## One-Time Setup

### 1. Create Global MCP Configuration

Run this command on your local machine (where Claude Code runs):

```bash
cat > ~/.mcp.json << 'EOF'
{
  "mcpServers": {
    "mcp": {
      "url": "http://192.168.68.100:8080/mcp/sse",
      "transport": "sse",
      "description": "Master MCP Orchestrator - Gateway to all services",
      "autoApprove": [
        "master.getServerInfo",
        "vector.collection.list",
        "vector.search.*",
        "docs.search",
        "docs.read",
        "cmdb.query",
        "crypto.market.*",
        "crypto.analysis.*"
      ]
    }
  }
}
EOF
```

### 2. Verify Configuration

```bash
# Check the file was created
cat ~/.mcp.json

# Test connection (from any directory)
curl http://192.168.68.100:8080/health
```

## Available Tools

Once connected to the master orchestrator, you have access to ALL tools:

### Vector Database (vector.*)
- `vector.collection.create` - Create collections
- `vector.collection.list` - List all collections
- `vector.document.add` - Add documents with embeddings
- `vector.search.semantic` - Semantic search
- `vector.search.cross_service` - Search across services

### Documentation (docs.*)
- `docs.search` - Search documentation
- `docs.create` - Create new documents
- `docs.read` - Read documents
- `docs.update` - Update documents
- `docs.list_versions` - Version history

### CMDB (cmdb.*)
- `cmdb.query` - Query configuration items
- `cmdb.get` - Get specific item
- `cmdb.add` - Add new items
- `cmdb.update` - Update items

### Linux Operations (os.linux.*)
- `os.linux.runCommand` - Execute commands
- `os.linux.readFile` - Read files
- `os.linux.writeFile` - Write files

### Crypto Trading (crypto.*)
- `crypto.market.price` - Get market prices
- `crypto.ta.indicators` - Technical analysis
- `crypto.analysis.trends` - Market trends
- `crypto.trade.simulate` - Paper trading

### AI Models (ai.models.*)
- `ai.models.chat` - Chat with AI models
- `ai.models.list` - List available models

### Kubernetes (infra.k8s.*)
- `infra.k8s.get_pods` - List pods
- `infra.k8s.get_services` - List services
- `infra.k8s.describe` - Describe resources

## Usage Examples

### From Any Project Directory

```bash
cd /path/to/any/project

# Claude Code now has access to all MCP tools
# Example prompts:

"Search for documentation about Docker setup"
# Uses: vector.search.semantic automatically

"What servers are running Redis?"  
# Uses: cmdb.query and vector.search.cross_service

"Show me the current Bitcoin price and RSI"
# Uses: crypto.market.price and crypto.ta.indicators

"Create a new document about deployment procedures"
# Uses: docs.create and vector.index.service
```

## Troubleshooting

### Connection Issues

1. **Check master is running:**
   ```bash
   docker ps | grep 00_master_mcp
   curl http://192.168.68.100:8080/health
   ```

2. **Check all services are up:**
   ```bash
   docker-compose ps
   ```

3. **View available namespaces:**
   ```bash
   curl http://192.168.68.100:8080/mcp/tools | jq
   ```

### Debug Mode

Add to ~/.mcp.json for debugging:
```json
{
  "mcpServers": {
    "mcp": {
      "url": "http://192.168.68.100:8000/mcp/sse",
      "transport": "sse",
      "debug": true
    }
  }
}
```

## Benefits of Master Connection

1. **Single Configuration**: Set once, use everywhere
2. **All Services Access**: Every tool available through one connection
3. **Namespace Organization**: Tools grouped by service (vector.*, docs.*, etc.)
4. **Workflow Support**: Master handles complex multi-service workflows
5. **No Port Management**: Don't need to remember individual service ports

## Advanced: Per-Project Override

If a specific project needs different settings, create a local `.mcp.json`:

```bash
cd /path/to/special/project
cat > .mcp.json << 'EOF'
{
  "mcpServers": {
    "mcp": {
      "url": "http://192.168.68.100:8000/mcp/sse",
      "transport": "sse",
      "autoApprove": ["*"]  // Auto-approve all tools for this project
    }
  }
}
EOF
```

## Next Steps

1. Ensure all MCP services are running
2. Create the global ~/.mcp.json file
3. Start using Claude Code from any directory!
4. All MCP tools will be available automatically
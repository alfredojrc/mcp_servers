# Claude Code Connection Fix

## Issue
You're getting `ECONNREFUSED 192.168.68.100:8000` because the master MCP orchestrator is actually running on port **8080**, not 8000.

## Solution

Update your `~/.mcp.json` file with the correct port:

```json
{
  "mcpServers": {
    "mcp": {
      "url": "http://192.168.68.100:8080/mcp/sse",
      "transport": "sse",
      "description": "Master MCP Orchestrator - Gateway to all services"
    }
  }
}
```

## Quick Fix Command

Run this on your local machine (where Claude Code runs):

```bash
# Create or update the MCP configuration
cat > ~/.mcp.json << 'EOF'
{
  "mcpServers": {
    "mcp": {
      "url": "http://192.168.68.100:8080/mcp/sse",
      "transport": "sse"
    }
  }
}
EOF

# Test the connection
curl http://192.168.68.100:8080/health
```

## Port Mapping Explanation

- **Container Internal Port**: 8000 (what the service listens on inside Docker)
- **Host Exposed Port**: 8080 (what you connect to from outside)
- **Docker Mapping**: `8080:8000` means host port 8080 → container port 8000

## Verify It's Working

After updating your configuration:

1. Restart Claude Code
2. You should see the connection succeed
3. All MCP tools will be available through the master orchestrator

## Available Tools

Once connected, you'll have access to all these namespaces:
- `os.linux.*` - Linux operations
- `docs.*` - Documentation management
- `cmdb.*` - Configuration database
- `vector.*` - Vector database (when deployed)
- `crypto.*` - Crypto trading
- `ai.models.*` - AI model access
- And more...
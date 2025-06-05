# MCP Configuration for Different Projects

## Configuration Scopes

Claude Code supports three MCP configuration scopes:

### 1. Project-Specific Configuration (Recommended for team projects)
```bash
# Navigate to your project directory
cd /path/to/your/project

# Add MCP server for this project only
claude mcp add --scope project mcp-orchestrator /data/mcp_servers/claude-mcp-wrapper.py
```

This creates a `.mcp.json` file in your project root that can be committed to version control.

### 2. User-Global Configuration (For personal use across all projects)
```bash
# Add MCP server globally for your user
claude mcp add --scope user mcp-orchestrator /data/mcp_servers/claude-mcp-wrapper.py
```

### 3. Local Session Configuration (Temporary, current terminal only)
```bash
# Add MCP server for current session
claude mcp add --scope local mcp-orchestrator /data/mcp_servers/claude-mcp-wrapper.py
```

## Examples for Different Scenarios

### Scenario 1: Different Project with Same MCP Server
```bash
cd /path/to/another/project
claude mcp add --scope project mcp-orchestrator /data/mcp_servers/claude-mcp-wrapper.py
```

### Scenario 2: Project with Custom MCP Server
```bash
cd /path/to/custom/project

# Add a custom MCP server with environment variables
claude mcp add --scope project custom-mcp /path/to/custom/mcp-server.py \
  -e API_KEY=your-key \
  -e CONFIG_PATH=/custom/config.json
```

### Scenario 3: SSE-based MCP Server
```bash
# For HTTP/SSE based servers
claude mcp add --scope project remote-mcp http://localhost:8080/sse \
  --transport sse \
  -H "Authorization: Bearer token123"
```

## Managing Project Configurations

### List all MCP servers (shows scope)
```bash
claude mcp list
```

### Remove project-specific server
```bash
claude mcp remove --scope project server-name
```

### Reset all project-specific approvals
```bash
claude mcp reset-project-choices
```

## Best Practices

1. **For Team Projects**: Use `--scope project` and commit `.mcp.json` to version control
2. **For Personal Projects**: Use `--scope user` for consistency across your projects
3. **For Testing**: Use `--scope local` (default) for temporary configurations

## Project .mcp.json Example

When you add an MCP server with `--scope project`, it creates `.mcp.json`:

```json
{
  "servers": {
    "mcp-orchestrator": {
      "command": "/data/mcp_servers/claude-mcp-wrapper.py",
      "transport": "stdio",
      "env": {},
      "args": []
    }
  }
}
```

## Copying Configuration to Another Project

```bash
# Option 1: Copy the wrapper script
cp /data/mcp_servers/claude-mcp-wrapper.py /new/project/path/
cd /new/project/path
claude mcp add --scope project local-mcp ./claude-mcp-wrapper.py

# Option 2: Reference the original location
cd /new/project/path
claude mcp add --scope project mcp-orchestrator /data/mcp_servers/claude-mcp-wrapper.py

# Option 3: Copy existing .mcp.json
cp /original/project/.mcp.json /new/project/
```
# Claude Code Integration Guide

## Overview

This document explains how Claude Code interacts with MCP servers and validates that our Documentation MCP Service can properly integrate with Claude Code.

## What is Claude Code?

Claude Code (available at claude.ai/code) is an AI coding assistant that can:
- Connect to MCP servers as a client
- Act as an MCP server itself
- Execute tools and manage workflows through the MCP protocol

## Integration Architecture

```
┌─────────────┐     MCP Protocol    ┌─────────────────────┐
│ Claude Code │ ◄─────────────────► │ Documentation MCP   │
│   (Client)  │     HTTP/SSE         │     (Server)        │
└─────────────┘                      └─────────────────────┘
       │                                      │
       │                                      ▼
       ▼                              ┌─────────────────┐
┌─────────────┐                       │ Document Store  │
│ User Files  │                       │  (Markdown)     │
└─────────────┘                       └─────────────────┘
```

## How Claude Code Connects to MCP Servers

### 1. Connection Methods

Claude Code can connect to MCP servers in three ways:

#### a) Project Configuration (.mcp.json)
```json
{
  "mcpServers": {
    "documentation": {
      "url": "http://192.168.68.100:8011/sse",
      "transport": "sse"
    }
  }
}
```

#### b) Claude Desktop Configuration
Located at `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "11_documentation_mcp": {
      "command": "docker",
      "args": ["exec", "-i", "mcp_servers_11_documentation_mcp_1", "python", "mcp_server.py"],
      "env": {}
    }
  }
}
```

#### c) Direct URL Connection
Claude Code can connect directly to:
- `http://localhost:8011/sse` (local)
- `http://192.168.68.100:8011/sse` (network)

### 2. Authentication & Security

- **OAuth Support**: For remote MCP servers on Claude.ai
- **Local Trust**: Claude Desktop trusts local MCP servers
- **Approval Tokens**: Our service can require approval for write operations

## Validation: Documentation MCP + Claude Code

### ✅ Compatible Features

1. **Protocol Support**
   - Our service implements MCP over HTTP/SSE
   - Uses JSON-RPC 2.0 format
   - Supports tool discovery and execution

2. **Tool Namespace**
   - All tools follow `docs.*` pattern
   - Compatible with Claude's tool discovery

3. **Response Format**
   - Returns structured JSON responses
   - Includes proper error handling
   - Supports streaming for large documents

### 🔧 Available Tools for Claude

```python
# Tools Claude Code can use:
docs.search          # Search documentation
docs.get             # Retrieve specific document
docs.list            # List documents by category
docs.create          # Create new documentation
docs.update          # Update existing docs
docs.categories.list # List available categories
docs.tags.list       # List all tags
docs.getMetrics      # Get usage metrics
```

## Integration Examples

### 1. Search Documentation
```python
# Claude Code can execute:
{
  "tool": "docs.search",
  "arguments": {
    "query": "API authentication",
    "category": "api",
    "tags": ["security", "auth"]
  }
}
```

### 2. Create Documentation
```python
# Claude Code can create docs:
{
  "tool": "docs.create",
  "arguments": {
    "title": "New Feature Guide",
    "content": "# Feature Documentation...",
    "category": "guides",
    "tags": ["feature", "tutorial"],
    "approval_token": "claude-generated"
  }
}
```

### 3. Update Documentation
```python
# Claude Code can update:
{
  "tool": "docs.update",
  "arguments": {
    "doc_id": "abc123",
    "content": "# Updated content...",
    "version_note": "Added examples",
    "approval_token": "claude-generated"
  }
}
```

## Setting Up Claude Code Integration

### Step 1: Ensure Service is Running
```bash
# Check if documentation service is accessible
curl http://192.168.68.100:8011/
# Should return the web interface
```

### Step 2: Configure Claude Code
Create `.mcp.json` in your project:
```json
{
  "mcpServers": {
    "documentation": {
      "url": "http://192.168.68.100:8011/sse",
      "transport": "sse",
      "autoApprove": ["docs.search", "docs.get", "docs.list"]
    }
  }
}
```

### Step 3: Test Integration
In Claude Code, try:
```
"Search for documentation about MCP architecture"
```

Claude should be able to:
1. Connect to the documentation service
2. Execute the search tool
3. Return relevant results

## Advanced Integration

### 1. Bidirectional Communication
Claude Code can:
- Read documentation and suggest improvements
- Create new docs based on code analysis
- Update docs when code changes

### 2. Workflow Automation
```python
# Example workflow Claude could execute:
1. Search for existing docs
2. Analyze code changes
3. Update relevant documentation
4. Create changelog entry
```

### 3. Context Preservation
- Claude maintains conversation context
- Can reference previous queries
- Builds knowledge over time

## Troubleshooting

### Common Issues

1. **Connection Failed**
   ```bash
   # Check service is running
   docker ps | grep documentation
   
   # Check port is accessible
   netstat -tuln | grep 8011
   ```

2. **Tool Not Found**
   ```bash
   # List available tools
   curl -X POST http://192.168.68.100:8011/messages \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}'
   ```

3. **Permission Denied**
   - Check `REQUIRE_APPROVAL` setting
   - Ensure approval tokens are provided

### Debug Mode
Run Claude Code with debug flag:
```bash
claude --mcp-debug
```

## Best Practices

### 1. Tool Design
- Keep tool names descriptive
- Use consistent parameter names
- Return structured data

### 2. Error Handling
- Provide clear error messages
- Include recovery suggestions
- Log errors for debugging

### 3. Performance
- Implement caching for frequent queries
- Use streaming for large responses
- Optimize search indices

## Security Considerations

### 1. Access Control
- Use approval tokens for write operations
- Implement rate limiting
- Log all modifications

### 2. Data Privacy
- Don't expose sensitive information
- Sanitize user inputs
- Encrypt data in transit

### 3. Prompt Injection Protection
- Validate all inputs
- Escape special characters
- Monitor for suspicious patterns

## Future Enhancements

### 1. AI-Powered Features
- Auto-categorization of documents
- Smart content suggestions
- Duplicate detection

### 2. Enhanced Integration
- VS Code extension
- GitHub integration
- CI/CD hooks

### 3. Analytics
- Usage patterns
- Popular searches
- Content gaps

## Conclusion

✅ **Validation Result**: The Documentation MCP Service is fully compatible with Claude Code and can be integrated seamlessly.

Key benefits:
- No additional API costs
- Local data control
- Real-time updates
- Bidirectional communication
- Context preservation

The integration enables Claude Code to become an intelligent documentation assistant that can help maintain, search, and improve your documentation automatically.

---

*Last Updated: June 2025*
*Version: 1.0*
# Claude MCP Configuration - The Definitive Guide

## Quick Reference / TL;DR

**⚠️ Key Alert:** The `@modelcontextprotocol/proxy` npm package **does NOT exist**. Do not attempt to use it. Any documentation referencing this package is incorrect.

### Working Configuration (Copy & Paste)

#### For Claude Desktop
Location: `~/.claude/claude_desktop_config.json` (Linux/Default), `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS), `%APPDATA%\\Claude\\claude_desktop_config.json` (Windows)
```json
{
  "mcpServers": {
    "mcp": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "mcp_master", // Your master orchestrator container name
        "python",
        "mcp_host_stdio_claude.py" // The STDIO script in your container
      ]
    }
  }
}
```

#### For Claude Code CLI
Location: `~/.mcp.json` (User-global) or `./.mcp.json` (Project-specific)
```json
{
  "mcpServers": {
    "mcp": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "mcp_master", // Your master orchestrator container name
        "python",
        "mcp_host_stdio_claude.py" // The STDIO script in your container
      ]
    }
  }
}
```
**Note**: Ensure `mcp_master` is the correct name of your running master orchestrator Docker container. Verify with `docker ps`. The script `mcp_host_stdio_claude.py` should exist within that container.

### Common Fixes
*   **"Connection closed" / Timeout issues / 400 Bad Request / 404 Not Found with `00_master_mcp`**:
    *   Ensure your Docker container (e.g., `mcp_servers_00_master_mcp_1` or your specific name for the master orchestrator) is running: `docker ps`.
    *   Check container logs for errors: `docker logs <your_master_container_name>`.
    *   **For detailed troubleshooting of `00_master_mcp` connection issues (including Docker sync, 400/404s, and the switch to direct SSE serving), see the dedicated section: [Mastering the `00_master_mcp` Orchestrator: Connection & Troubleshooting](#mastering-the-00_master_mcp-orchestrator-connection--troubleshooting).**
    *   If using remote Docker, VMs, or complex network setups, ensure IP addresses/hostnames are correct and firewalls allow necessary connections to the Docker daemon or container.
*   **"No servers configured" / Changes not taking effect**:
    *   Restart Claude Desktop or your terminal session for Claude Code completely after any configuration changes.
    *   Verify the JSON syntax in your configuration file is correct.
    *   Ensure you are editing the correct configuration file for your OS and Claude product (Desktop vs. Code CLI).
*   **Container not found / Script not found**:
    *   Verify the exact container name with `docker ps`.
    *   Confirm the path to `mcp_host_stdio_claude.py` is correct within the container.

---

## Overview

This guide consolidates all learnings from hours of troubleshooting to provide a working MCP (Model Context Protocol) configuration for Claude Desktop and Claude Code. 

**Key Insight**: Claude Desktop/Code has limited SSE support. The most reliable approach is using STDIO transport via the MCP proxy.

## Prerequisites

1. Docker and Docker Compose installed
2. MCP services running: `docker-compose up -d`
3. Node.js installed (for npx command)

## Working Configuration Methods

### Method 1: Direct Docker STDIO (Recommended) ✅

**IMPORTANT UPDATE**: The `@modelcontextprotocol/proxy` package does not exist. Use this working method instead. This is the most reliable approach.

#### For Claude Desktop (GUI Application)

1. **Edit configuration file**:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Linux: `~/.claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add this configuration**:
```json
{
  "mcpServers": {
    "mcp": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "mcp_master",
        "python",
        "mcp_host_stdio_claude.py"
      ]
    }
  }
}
```

#### For Claude Code (CLI)

Edit `~/.mcp.json` (for user-global) or `./.mcp.json` (for project-specific, created via `claude mcp add --scope project ...`):
```json
{
  "mcpServers": {
    "mcp": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "mcp_master",
        "python",
        "mcp_host_stdio_claude.py"
      ]
    }
  }
}
```

### Method 2: Custom STDIO Bridge (Alternative if Direct Docker STDIO Fails)

If Method 1 (Direct Docker STDIO) presents issues, or if you prefer a Node.js based bridge, this custom solution can be used. It relies on a local Node.js script to connect to your MCP server's SSE endpoint and bridge it to STDIO for Claude.

**Prerequisites for this method:**
*   Node.js and npm installed.
*   The `eventsource` package: `npm install eventsource` (you might want to install this globally or within a specific project context where you run the bridge).
*   Your MCP master orchestrator must be exposing an HTTP/SSE endpoint (e.g., `http://localhost:8000/sse`).

**Example `mcp-stdio-client.js` script (save this to e.g., `/data/mcp_servers/mcp-stdio-client.js`):**
```javascript
// Example mcp-stdio-client.js
// (Ensure you have 'eventsource' installed: npm install eventsource)
const EventSource = require('eventsource');
const readline = require('readline');

if (process.argv.length < 3) {
  console.error('Usage: node mcp-stdio-client.js <SSE_URL>');
  process.exit(1);
}

const sseUrl = process.argv[2];
const es = new EventSource(sseUrl);

es.onmessage = function (event) {
  process.stdout.write(event.data + '\\n');
};

es.onerror = function (err) {
  console.error('EventSource failed:', err);
  es.close();
};

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

rl.on('line', function(line){
  // For now, this simple bridge just logs incoming stdin
  // A real implementation would need to POST this to an MCP endpoint
  // or handle it according to MCP's STDIO communication patterns if the server expects client messages.
  // This example focuses on receiving from server via SSE and outputting to STDOUT.
  // console.error('Received from Claude (stdin):', line);
});

// Keep alive, or handle specific close conditions
// process.stdin.resume(); // This might not be ideal
```

**Configuration for Claude (Desktop or Code CLI - adjust path to script):**
```json
{
  "mcpServers": {
    "mcp-custom-bridge": {
      "command": "node",
      "args": [
        "/path/to/your/mcp-stdio-client.js", // Adjust to actual path
        "http://localhost:8000/sse" // Your MCP server's SSE endpoint
      ]
      // "type": "stdio" // for Claude Code CLI if not inferred
    }
  }
}
```
**Note on Custom Bridge:** The example `mcp-stdio-client.js` is basic. A robust implementation would need to handle bidirectional communication if your MCP server expects input from Claude via STDIO, not just sending data to Claude. This method is more complex than Direct Docker STDIO.

### Method 3: Wrapper Script (Previously Method 2)

If you have a wrapper script at `/data/mcp_servers/mcp-orchestrator`:

```json
{
  "mcpServers": {
    "mcp": {
      "command": "/data/mcp_servers/mcp-orchestrator"
    }
  }
}
```

## Troubleshooting

### Common Issues and Solutions

1.  **"MCP error -32000: Connection closed", "400 Bad Request", "404 Not Found" (especially with `00_master_mcp`)**
    *   Ensure Docker containers are running: `docker ps`
    *   Check container logs, especially for `00_master_mcp`: `docker logs <your_master_container_name>`
    *   Verify the `00_master_mcp` is serving on the correct endpoint (likely `http://<host>:PORT/sse`).
    *   **Refer to the detailed guide for `00_master_mcp` setup: [Mastering the `00_master_mcp` Orchestrator: Connection & Troubleshooting](#mastering-the-00_master_mcp-orchestrator-connection--troubleshooting).**

2. **"@modelcontextprotocol/proxy not found"**
   - **This package does not exist!** Use Method 1 (Direct Docker STDIO) instead
   - The documentation referencing this package is incorrect

3. **Connection timeouts**
   - Use your machine's IP address, not localhost
   - Check firewall settings
   - Verify port 8000 is accessible

4. **"No MCP servers configured"**
   - Restart Claude Desktop/Code after configuration
   - Verify JSON syntax is correct
   - Check file permissions on config file

### Testing Your Configuration

1. **Test SSE endpoint**:
```bash
curl -N http://YOUR_IP:8000/sse
```

2. **Test STDIO script directly**:
```bash
echo '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "1.0", "clientInfo": {"name": "test", "version": "1.0"}, "capabilities": {}}, "id": 1}' | docker exec -i mcp_master python mcp_host_stdio_claude.py
```

3. **In Claude Desktop/Code**:
   - Type `/mcp` to see server status
   - Ask "What MCP tools are available?"

## Key Differences

### Claude Desktop vs Claude Code

| Feature | Claude Desktop | Claude Code |
|---------|---------------|-------------|
| Config Location | JSON file | CLI commands or .mcp.json |
| Config Format | claude_desktop_config.json | `claude mcp add` command |
| Transport Support | STDIO preferred | STDIO preferred |
| SSE Support | Limited | Limited |

### Configuration File Formats

**Claude Desktop** (`claude_desktop_config.json`):
- No `type` field needed (STDIO is implied)
- Uses `command` and `args` fields

**Claude Code** (`.mcp.json`):
- Can specify `type: "stdio"` or `type: "sse"`
- Supports project/user/local scopes

## Multiple Services Configuration

To configure multiple MCP services:

```json
{
  "mcpServers": {
    "orchestrator": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/proxy", "http://YOUR_IP:8000/sse"]
    },
    "documentation": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/proxy", "http://YOUR_IP:8011/sse"]
    },
    "kubernetes": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/proxy", "http://YOUR_IP:8008/sse"]
    }
  }
}
```

## Security Considerations

1. **Trust**: Only use MCP servers you trust
2. **Network**: Use specific IPs instead of 0.0.0.0
3. **Permissions**: Run containers with minimal privileges
4. **Secrets**: Never expose API keys in configuration

## Quick Start Checklist

- [ ] Docker containers running (`docker ps`)
- [ ] Know your machine's IP address (`ip addr` or `ifconfig`)
- [ ] Claude Desktop/Code installed
- [ ] Configuration file created with proxy method
- [ ] Application restarted after configuration
- [ ] Test with `/mcp` command

## Still Having Issues?

1. Check container logs: `docker logs -f mcp_master`
2. Verify network connectivity to port 8000
3. Try each configuration method in order
4. Ensure you're using the correct config file location
5. Check that JSON syntax is valid

---

## Mastering the `00_master_mcp` Orchestrator: Connection & Troubleshooting

This section details the journey to establish a stable and functional connection between the Claude Code CLI and the `00_master_mcp` orchestrator service. The orchestrator is critical as it runs the main FastMCP server, hosts the `WorkflowEngine`, and proxies requests to other downstream MCP services.

### Initial State: The Elusive Connection (The 404/400 Saga)

The initial attempts to connect the Claude Code CLI to the `00_master_mcp` (running in Docker) were fraught with difficulties:

1.  **Docker Sync Issues & Stale Code:** A primary hurdle was ensuring that changes made to `00_master_mcp/mcp_host.py` on the host machine were correctly reflected inside the Docker container. Incorrect `Dockerfile` `COPY` paths and potential volume mount issues meant the container often ran an outdated version of the server code, leading to confusing behavior and masking the real problems.
    *   **Lesson:** Always verify that the exact code you intend to run is what the container is executing. Docker logs, `docker exec cat <file>`, and careful `Dockerfile` review are crucial.

2.  **404 Not Found Errors:** Early on, the `/health` and `/mcp/` endpoints returned 404s. This was traced to:
    *   The `entrypoint.sh` script in the `00_master_mcp` container initially attempting to execute a deleted Python file (`mcp_host_simple.py`).
    *   Correcting `entrypoint.sh` to `exec uvicorn mcp_host:main_app ...` (when `mcp_host.py` was structured as a Starlette app with `FastMCP` mounted) still led to 404s, often due to the stale code issue mentioned above.

3.  **Persistent "400 Bad Request" from Claude Code CLI:** Once the 404s were seemingly resolved and an ultra-minimal Starlette/FastMCP server was confirmed to be running (by meticulously checking Docker logs and `mcp_host.py` content within the container), the Claude Code CLI began consistently reporting a "400 Bad Request" when targeting `http://localhost:8000/mcp/`.
    *   Server-side Uvicorn logs would show `FastMCP`'s `streamable_http_manager` creating a transport session, immediately followed by the 400 error.
    *   Attempts to reorder `FastMCP` initialization, comment out middleware, or simplify the full `mcp_host.py` (when it was incorrectly running the full version due to sync issues) did not resolve this.

4.  **The "406 Not Acceptable" Clue:** A pivotal moment occurred when a direct browser connection to the `/mcp/` endpoint (from a machine on the local network) briefly yielded a client-side MCP error: `{ code: -32600, message: "Not Acceptable: Client must accept text/event-stream" }`. The server logs simultaneously showed a "406 Not Acceptable" from the browser's IP and a "400 Bad Request" from the Docker internal IP (presumed to be the CLI). This highlighted a potential issue with SSE header negotiation or how `FastMCP` was being served.

### The Breakthrough: Direct SSE with `mcp_app.run()`

The "406 Not Acceptable" error and the persistent 400s suggested that mounting `FastMCP().http_app()` within a Starlette application (`app.mount("/mcp", mcp_app.http_app())`) might be causing issues with how SSE connections were handled or how FastMCP expected to be run for SSE.

The solution was to switch `00_master_mcp/mcp_host.py` to use `FastMCP`'s direct run capability for SSE:

1.  **Simplified `mcp_host.py`:**
    ```python
    # Ultra-minimal mcp_host.py for testing direct SSE run
    from fastmcp import FastMCP
    import logging

    logging.basicConfig(level=logging.DEBUG, force=True)
    logger = logging.getLogger(__name__)

    mcp_app = FastMCP(
        name="Minimal SSE Test",
        protocol_version="2024-11-05",
        debug=True
    )

    if __name__ == "__main__":
        logger.info("Starting FastMCP server directly using mcp_app.run() with SSE transport...")
        mcp_app.run(
            transport="sse", 
            host="0.0.0.0", 
            port=8000, 
            log_level="debug"
        )
    ```

2.  **Updated `entrypoint.sh`:**
    The `00_master_mcp/entrypoint.sh` was changed to execute the Python script directly:
    ```sh
    #!/bin/sh
    set -e
    echo "--- Master Orchestrator Entrypoint (Direct FastMCP Run) ---"
    echo "Executing Python script directly: python /workspace/mcp_host.py"
    exec python /workspace/mcp_host.py > /workspace/mcp_host.log 2>&1
    ```

3.  **Client Reconfiguration:** The Claude Code CLI (and any other client) now needed to target `http://localhost:8000/sse` (or the appropriate IP and port, and `/sse` path).

**Result:** With these changes, after rebuilding the Docker image and restarting the container, the Claude Code CLI successfully connected to the `00_master_mcp` service! The server logs confirmed `FastMCP` was listening on `http://0.0.0.0:8000/sse`, and the client connecting to this endpoint no longer received a 400 error.

### Restoring Full Orchestrator Functionality

With the connection mystery solved, the full application logic was reintroduced into `00_master_mcp/mcp_host.py`, while retaining the `mcp_app.run(transport="sse", ...)` method:

*   **`MCPServiceClient`:** For making calls to downstream MCP services (e.g., `01_linux_cli_mcp`).
*   **`WorkflowEngine`:** To execute multi-step workflows defined by sequences of tool calls.
*   **Tool Definitions:** Re-registration of tools like `orchestrator.executeWorkflow`, `system.health`, and `system.listServices`.
*   **Proxy Configuration:** `FastMCP` was configured with `mcp_servers` to proxy direct calls to known downstream service namespaces.
*   **HTTP Health Endpoint:** A simple `/health` route was added to the `FastMCP` app for basic service health checks.
*   **Lifespan Management:** An `async` lifespan function was added to manage the startup and shutdown of resources, like closing the `httpx.AsyncClient` used by `MCPServiceClient`.

The `entrypoint.sh` remained the same, executing `python /workspace/mcp_host.py`.

### Current Working Configuration for `00_master_mcp`

*   **`00_master_mcp/mcp_host.py`:** Contains the full orchestrator logic, with `FastMCP` initialized with all tools, resources, and proxy settings. It is started using `mcp_app.run(transport="sse", host="0.0.0.0", port=8000, log_level="debug")`.
*   **`00_master_mcp/entrypoint.sh`:** Executes `exec python /workspace/mcp_host.py ...`.
*   **`00_master_mcp/Dockerfile`:** Correctly `COPY`s `mcp_host.py` and `entrypoint.sh` to `/workspace/`.
*   **Claude Code CLI Configuration (`~/.mcp.json` or project `.mcp.json`):**
    Must point to the `/sse` endpoint. Example for HTTP connection (replace `mcp_master` with your orchestrator's HTTP endpoint if not using STDIO bridge for the main orchestrator):
    ```json
    {
      "mcpServers": {
        "orchestrator": { // Or your preferred namespace for the main orchestrator
          "url": "http://localhost:8000/sse", // Or IP:PORT/sse
          "protocol_version": "2024-11-05" 
        }
        // ... other STDIO-bridged services like mcp_host_stdio_claude.py if still needed ...
        // "mcp": {
        //   "type": "stdio",
        //   "command": "docker",
        //   "args": [
        //     "exec", "-i", "mcp_servers_00_master_mcp_1", // actual container name
        //     "python", "mcp_host_stdio_claude.py" 
        //   ]
        // }
      }
    }
    ```
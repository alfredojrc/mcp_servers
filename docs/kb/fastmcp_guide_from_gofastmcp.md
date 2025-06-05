# FastMCP Guide (from gofastmcp.com)

This guide provides a comprehensive overview of FastMCP, drawing from the official documentation at [gofastmcp.com](https://gofastmcp.com). It covers getting started, server functionalities like proxying and OpenAPI integration, client usage, and various patterns.

## 1. Introduction to FastMCP & MCP

(Content primarily from `gofastmcp.com/getting-started/welcome`)

The Model Context Protocol (MCP) is a new, standardized way to provide context and tools to your LLMs. FastMCP makes building MCP servers and clients simple and intuitive.

### What is MCP?

The Model Context Protocol lets you build servers that expose data and functionality to LLM applications in a secure, standardized way. It is often described as "the USB-C port for AI", providing a uniform way to connect LLMs to resources they can use. It may be easier to think of it as an API, but specifically designed for LLM interactions. MCP servers can:

*   Expose data through **Resources** (think of these sort of like GET endpoints; they are used to load information into the LLM's context)
*   Provide functionality through **Tools** (sort of like POST endpoints; they are used to execute code or otherwise produce a side effect)
*   Define interaction patterns through **Prompts** (reusable templates for LLM interactions)
*   And more!

There is a low-level Python SDK available for implementing the protocol directly, but FastMCP aims to make that easier by providing a high-level, Pythonic interface.

FastMCP 1.0 was so successful that it is now included as part of the official MCP Python SDK!

### Why FastMCP?

The MCP protocol is powerful but implementing it involves a lot of boilerplate - server setup, protocol handlers, content types, error management. FastMCP handles all the complex protocol details and server management, so you can focus on building great tools. It's designed to be high-level and Pythonic; in most cases, decorating a function is all you need.

FastMCP aims to be:

*   🚀 **Fast**: High-level interface means less code and faster development
*   🍀 **Simple**: Build MCP servers with minimal boilerplate
*   🐍 **Pythonic**: Feels natural to Python developers
*   🔍 **Complete**: FastMCP aims to provide a full implementation of the core MCP specification

**FastMCP v1** focused on abstracting the most common boilerplate of exposing MCP server functionality, and is now included in the official MCP Python SDK. **FastMCP v2** expands on that foundation to introduce novel functionality mainly focused on simplifying server interactions, including flexible clients, proxying and composition, and deployment.

## 2. Getting Started

### Installation

(Content from `gofastmcp.com/getting-started/installation`)

We recommend using `uv` to install and manage FastMCP.

If you plan to use FastMCP in your project, you can add it as a dependency with:

```bash
uv add fastmcp
```

Alternatively, you can install it directly with `pip` or `uv pip`:

Using `uv pip`:
```bash
uv pip install fastmcp
```

Using `pip`:
```bash
pip install fastmcp
```

#### Verify Installation

To verify that FastMCP is installed correctly, you can run the following command:

```bash
fastmcp version
```

You should see output like the following:

```bash
$ fastmcp version

FastMCP version:   0.4.2.dev41+ga077727.d20250410
MCP version:                                1.6.0
Python version:                            3.12.2
Platform:            macOS-15.3.1-arm64-arm-64bit
FastMCP root path:            ~/Developer/fastmcp
```
*(Note: Version numbers and paths will vary based on your specific installation.)*

#### Installing for Development

If you plan to contribute to FastMCP:

```bash
git clone https://github.com/jlowin/fastmcp.git
cd fastmcp
uv sync
```
This installs all dependencies, including development ones, and creates a virtual environment.
To run tests:
```bash
pytest
```

### Quickstart

(Content from `gofastmcp.com/getting-started/quickstart` and `welcome`)

Create tools, expose resources, define prompts, and more with clean, Pythonic code:

```python
from fastmcp import FastMCP

mcp = FastMCP("Demo 🚀")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

if __name__ == "__main__":
    mcp.run()
```

## 3. FastMCP Servers

(Content from `gofastmcp.com/servers/fastmcp`)

The central piece of a FastMCP application is the `FastMCP` server class. This class acts as the main container for your application's tools, resources, and prompts, and manages communication with MCP clients.

### Core Components

(Refer to `gofastmcp.com/servers/tools`, `resources`, `prompts`, `context` for full details. Below is a conceptual overview.)

*   **Tools**: Define functions that LLMs can call to perform actions. Decorated with `@mcp.tool()`.
*   **Resources**: Expose data that LLMs can read to gain context. Decorated with `@mcp.resource()`.
*   **Prompts**: Reusable templates for LLM interactions. Defined using `mcp.prompt()`.
*   **Context**: Provides a way to manage and share state or data across tool calls or resource access within a session.

### Proxy Servers

(Content from `gofastmcp.com/servers/proxy`)

Use FastMCP to act as an intermediary or change transport for other MCP servers. (New in FastMCP v2.0.0)

FastMCP provides a powerful proxying capability that allows one FastMCP server instance to act as a frontend for another MCP server. This is achieved using the `FastMCP.as_proxy()` class method. `as_proxy()` accepts either an existing `Client` or any argument that can be passed to a `Client` as its `transport` parameter—such as another `FastMCP` instance, a URL to a remote server, or an MCP configuration dictionary.

#### What is Proxying?

Proxying means setting up a FastMCP server that doesn't implement its own tools or resources directly. Instead, when it receives a request (like `tools/call` or `resources/read`), it forwards that request to a *backend* MCP server, receives the response, and then relays that response back to the original client.

#### Use Cases

*   **Transport Bridging**: Expose a server running on one transport (e.g., a remote SSE server) via a different transport (e.g., local Stdio for Claude Desktop).
*   **Adding Functionality**: Insert a layer in front of an existing server to add caching, logging, authentication, or modify requests/responses (though direct modification requires subclassing `FastMCPProxy`).
*   **Security Boundary**: Use the proxy as a controlled gateway to an internal server.
*   **Simplifying Client Configuration**: Provide a single, stable endpoint (the proxy) even if the backend server's location or transport changes.

#### Creating a Proxy

The easiest way to create a proxy is using the `FastMCP.as_proxy()` class method.

```python
from fastmcp import FastMCP, Client

# Provide the backend in any form accepted by Client
proxy_server = FastMCP.as_proxy(
    "backend_server.py",  # Could also be a FastMCP instance, config dict, or a remote URL
    name="MyProxyServer"  # Optional settings for the proxy
)

# Or create the Client yourself for custom configuration
# backend_client = Client("backend_server.py") # Example for a local script
# proxy_from_client = FastMCP.as_proxy(backend_client)
```

**How `as_proxy` Works:**
1.  It connects to the backend server using the provided client information.
2.  It discovers all the tools, resources, resource templates, and prompts available on the backend server.
3.  It creates corresponding "proxy" components that forward requests to the backend.
4.  It returns a standard `FastMCP` server instance.

*(Note: Proxying primarily focuses on tools, resources, templates, and prompts. Advanced features like notifications/sampling might have limited support in current versions.)*

#### Bridging Transports

Example: Making a remote SSE server available locally via Stdio:
```python
from fastmcp import FastMCP

# Target a remote SSE server directly by URL
proxy = FastMCP.as_proxy("http://example.com/mcp/sse", name="SSE to Stdio Proxy")

# if __name__ == "__main__":
#     proxy.run() # Runs via Stdio by default
```

#### In-Memory Proxies

Proxy an in-memory `FastMCP` instance:
```python
from fastmcp import FastMCP

# Original server
original_server = FastMCP(name="Original")

@original_server.tool()
def tool_a() -> str:
    return "A"

# Create a proxy of the original server directly
proxy = FastMCP.as_proxy(
    original_server,
    name="Proxy Server"
)
```

#### Configuration-Based Proxies
(New in FastMCP v2.4.0)

Create a proxy from an MCPConfig dictionary:
```python
from fastmcp import FastMCP

# Single server config
config_single = {
    "mcpServers": {
        "default": {
            "url": "https://example.com/mcp",
            "transport": "streamable-http"
        }
    }
}
proxy_single = FastMCP.as_proxy(config_single, name="Config-Based Proxy")

# Multi-server configuration
config_multi = {
    "mcpServers": {
        "weather": {
            "url": "https://weather-api.example.com/mcp",
            "transport": "streamable-http"
        },
        "calendar": {
            "url": "https://calendar-api.example.com/mcp",
            "transport": "streamable-http"
        }
    }
}
composite_proxy = FastMCP.as_proxy(config_multi, name="Composite Proxy")
# Tools/resources accessed with prefixes like: weather_get_forecast, calendar://calendar/events/today

# if __name__ == "__main__":
#     proxy_single.run()
#     # composite_proxy.run()
```
*(Note: The MCPConfig format may evolve.)*

#### `FastMCPProxy` Class
Internally, `FastMCP.as_proxy()` uses the `FastMCPProxy` class. Direct interaction is typically for advanced scenarios like subclassing to add custom logic.

### Composition
(Refer to `gofastmcp.com/servers/composition` for full details.)
FastMCP allows building modular applications by mounting multiple `FastMCP` instances onto a parent server using `mcp.mount()` or `mcp.import_server()`.

### OpenAPI & FastAPI Integration
(Content from `gofastmcp.com/servers/openapi`)

Automatically generate FastMCP servers from existing OpenAPI specifications or FastAPI applications.

#### FastAPI Integration
(New in FastMCP v2.0.0)
Convert FastAPI applications into MCP servers. (Requires `fastapi` to be installed separately).
```python
from fastapi import FastAPI
from fastmcp import FastMCP

# Your FastAPI app
app = FastAPI(title="My API", version="1.0.0")

@app.get("/items", tags=["items"], operation_id="list_items")
def list_items():
    return [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

@app.get("/items/{item_id}", tags=["items", "detail"], operation_id="get_item")
def get_item(item_id: int):
    return {"id": item_id, "name": f"Item {item_id}"}

# Convert FastAPI app to MCP server
mcp_server_from_fastapi = FastMCP.from_fastapi(app=app)

# if __name__ == "__main__":
#     mcp_server_from_fastapi.run()
```
All OpenAPI integration features (route mapping, customizing components, etc.) work with FastAPI apps.
Benefits: Zero code duplication, schema inheritance, ASGI transport (in-memory communication), full FastAPI features.

### Authentication
(Refer to `gofastmcp.com/servers/authentication` for full details.)
FastMCP provides built-in authentication support to secure server endpoints and authenticate clients.

## 4. Deployment

### Running the Server
(Refer to `gofastmcp.com/deployment/running-server` for full details.)
The main way to run a FastMCP server is by calling the `run()` method:
```python
# server.py
from fastmcp import FastMCP

mcp = FastMCP("My Server")
# ... define tools, resources ...

if __name__ == "__main__":
    mcp.run() # Default: uses STDIO transport
```
Supported transports:
*   **STDIO (Default)**: For local tools, CLI scripts. `mcp.run(transport="stdio")`
*   **Streamable HTTP**: Recommended for web deployments. `mcp.run(transport="streamable-http", host="127.0.0.1", port=8000, path="/mcp")`
*   **SSE**: For compatibility with existing SSE clients. `mcp.run(transport="sse", host="127.0.0.1", port=8000)`

### ASGI Integration
(Refer to `gofastmcp.com/deployment/asgi-integration` for full details.)
FastMCP servers can be run as ASGI applications, allowing integration with ASGI servers like Uvicorn or Hypercorn.

## 5. FastMCP Clients
(Content primarily from `gofastmcp.com/clients/overview`, `transports`, `authentication`, `advanced-features`)

FastMCP includes a `Client` class for interacting with MCP servers.

### Overview & Transports
The `Client` can connect to servers using various transports (Stdio, SSE, Streamable HTTP).
```python
from fastmcp import Client

# Connect to a server running via a Python script (stdio)
client_stdio = Client("path/to/your_server_script.py")

# Connect to a remote SSE server
client_sse = Client("http://example.com/mcp/sse")

# Connect to a remote Streamable HTTP server
client_http = Client("http://example.com/mcp/http") # Adjust path as needed
```

### Authentication
Clients can be configured with authentication mechanisms (e.g., Bearer tokens) to connect to secured MCP servers.
```python
from fastmcp import Client
from fastmcp.client.auth import BearerAuth

client_auth = Client(
    "https://api.example.com/mcp", # or /sse, /http
    auth=BearerAuth(token="your-access-token")
)
```

## 6. Integrations

### Anthropic / Claude Desktop
(Content from `gofastmcp.com/integrations/claude-desktop` and `contrib`)

Claude Desktop primarily supports local STDIO servers. FastMCP's proxy capability is key for using remote servers or servers with different transports with Claude Desktop.

**Proxying Remote Servers for Claude Desktop:**
Create a proxy server script that connects to your target remote server and runs itself via STDIO.

`proxy_for_claude.py`:
```python
from fastmcp import FastMCP, Client
from fastmcp.client.auth import BearerAuth # If auth is needed

# Example: Proxying a remote SSE server
REMOTE_URL = "https://example.com/mcp/sse"
# For an authenticated server:
# AUTH_TOKEN = "your-secret-token"
# client_to_remote = Client(REMOTE_URL, auth=BearerAuth(token=AUTH_TOKEN))
# proxy = FastMCP.as_proxy(client_to_remote, name="Authenticated Remote Proxy")

# For a non-authenticated server:
proxy = FastMCP.as_proxy(REMOTE_URL, name="Remote Server Proxy for Claude")

if __name__ == "__main__":
    proxy.run()  # Runs via STDIO, suitable for Claude Desktop
```
Then, configure this `proxy_for_claude.py` script in your Claude Desktop MCP settings.

### Other Integrations
FastMCP also has documentation for integrations with:
*   OpenAI (Refer to `gofastmcp.com/integrations/openai`)
*   Gemini SDK (Refer to `gofastmcp.com/integrations/gemini`)
*   Contrib Modules (Refer to `gofastmcp.com/integrations/contrib`)

## 7. Patterns & CLI

### Common Patterns
(Refer to `gofastmcp.com/patterns/...` for specific pages like `decorating-methods`, `http-requests`, `testing`)
*   **Decorating Methods**: The core way to define tools and resources.
*   **HTTP Requests**: Examples of tools that make HTTP requests.
*   **Testing**: Strategies for testing FastMCP servers.

### FastMCP CLI
(From `gofastmcp.com/getting-started/installation` and general knowledge)
FastMCP provides a command-line interface. A key command is:
*   `fastmcp version`: Displays version information for FastMCP, MCP, Python, and the platform.

This guide should provide a solid foundation for working with FastMCP. For the most detailed and up-to-date information, always consult the official documentation at [gofastmcp.com](https://gofastmcp.com). 
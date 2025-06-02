# Model Context Protocol (MCP) - Overview

## What is MCP?

The Model Context Protocol (MCP) is an open standard created by Anthropic in November 2024 that enables seamless integration between Large Language Models (LLMs) and external data sources and tools. Think of MCP like a USB-C port for AI applications - providing a standardized way to connect AI models to different data sources and tools.

## Key Concepts

### The MxN Problem
MCP solves the "MxN problem" - the combinatorial difficulty of integrating M different LLMs with N different tools. Instead of building custom integrations for each combination, MCP provides a standard protocol that both LLM vendors and tool builders can follow.

### Architecture
MCP uses a client-server architecture:
- **MCP Clients**: AI applications (like Claude Desktop, IDEs) that connect to servers
- **MCP Servers**: Services that expose data sources or tools through the MCP protocol
- **Communication**: JSON-RPC 2.0 messages over various transports (stdio, HTTP/SSE)

## Core Capabilities

MCP defines three primary capabilities that servers can expose:

### 1. Resources
- **Purpose**: Foundational data and information that the MCP server can access
- **Use Case**: Exposing files, databases, APIs as readable resources
- **Example**: Database tables, configuration files, documentation

### 2. Tools
- **Purpose**: Individual, specific actions or functionalities that the MCP server can execute
- **Use Case**: Running commands, transforming data, calling APIs
- **Example**: `load_data()`, `execute_query()`, `send_notification()`

### 3. Prompts
- **Purpose**: Agentic workflows or "recipes" for repeatable solutions
- **Use Cases**:
  - Guide discovery of server capabilities
  - List available resources, tools, and other prompts
  - Orchestrate sequences of tool calls
  - Prime the agent's memory with essential info
  - Provide suggestions and next steps
- **Example**: A "database analysis" prompt that discovers tables, analyzes schemas, and suggests queries

## Protocol Specification

### Message Flow
The protocol deliberately reuses message-flow ideas from the Language Server Protocol (LSP):
1. Client connects to server
2. Server advertises capabilities
3. Client requests resources/tools/prompts
4. Server executes and returns results

### Primitives
- **Server Primitives**: Prompts, Resources, Tools
- **Client Primitives**: Roots, Sampling

## Adoption and Ecosystem

### Official Support
- **Anthropic**: Native support in Claude Desktop
- **OpenAI**: Announced MCP support
- **Google DeepMind**: Integration planned
- **Microsoft**: Official C# SDK development

### Development Tools
- **Zed, Replit, Codeium, Sourcegraph**: IDE integrations
- **Block, Apollo**: Enterprise system integrations

### Pre-built Servers
Anthropic maintains reference implementations for:
- Google Drive, Slack, GitHub
- Git, PostgreSQL, MySQL
- Puppeteer, Stripe
- Docker integration

## Implementation

### SDKs Available
- TypeScript (official)
- Python (official)
- C# (Microsoft partnership)
- Java (community)

### Docker Integration
Docker provides special support for MCP:
- **Docker MCP Catalog**: Part of Docker Hub with 100+ verified tools
- **Containerized servers**: Run MCP servers in isolated containers
- **Security**: Built-in secrets management for secure token passing
- **Dynamic tools**: One Docker MCP server can manage multiple containerized tools

## Benefits

1. **Standardization**: Single protocol instead of custom integrations
2. **Security**: Controlled access with proper authentication
3. **Scalability**: Easy to add new tools and data sources
4. **Interoperability**: Any MCP client can use any MCP server
5. **Developer Experience**: Simple SDKs and clear specification

## Resources

- **Official Site**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **GitHub**: [github.com/modelcontextprotocol](https://github.com/modelcontextprotocol)
- **Specification**: [modelcontextprotocol.io/specification](https://modelcontextprotocol.io/specification)
- **Documentation**: [docs.anthropic.com/en/docs/agents-and-tools/mcp](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)
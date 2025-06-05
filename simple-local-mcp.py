#!/usr/bin/env python3
"""
Simple local MCP server for testing with Claude Code
"""

from fastmcp import FastMCP
import os

# Create MCP server
mcp = FastMCP("simple-local-mcp")

@mcp.tool("test.hello")
async def hello(name: str = "World") -> str:
    """Simple test tool that says hello"""
    return f"Hello, {name}! This is from the local MCP server."

@mcp.tool("test.echo")
async def echo(message: str) -> str:
    """Echo back the message"""
    return f"Echo: {message}"

@mcp.tool("file.list")
async def list_files(path: str = ".") -> str:
    """List files in a directory"""
    try:
        files = os.listdir(path)
        return f"Files in {path}:\n" + "\n".join(f"- {f}" for f in files[:20])
    except Exception as e:
        return f"Error listing files: {e}"

@mcp.tool("file.read")
async def read_file(path: str) -> str:
    """Read a file's contents"""
    try:
        with open(path, 'r') as f:
            content = f.read()
            if len(content) > 1000:
                content = content[:1000] + "\n... (truncated)"
            return content
    except Exception as e:
        return f"Error reading file: {e}"

if __name__ == "__main__":
    # Run with stdio transport for Claude Code
    mcp.run(transport="stdio")
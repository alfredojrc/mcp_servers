#!/usr/bin/env python3
import sys
import json
from typing import Any

def send_message(msg: dict):
    """Send a JSON-RPC message."""
    content = json.dumps(msg)
    sys.stdout.write(f"Content-Length: {len(content)}\r\n\r\n{content}")
    sys.stdout.flush()

def read_message():
    """Read a JSON-RPC message."""
    # Read Content-Length header
    line = sys.stdin.readline()
    if not line:
        return None
    
    # Parse content length
    content_length = int(line.split(": ")[1])
    
    # Read blank line
    sys.stdin.readline()
    
    # Read content
    content = sys.stdin.read(content_length)
    return json.loads(content)

def main():
    while True:
        msg = read_message()
        if not msg:
            break
        
        # Handle initialize
        if msg.get("method") == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": msg["id"],
                "result": {
                    "protocolVersion": "0.1.0",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "simple-mcp",
                        "version": "1.0.0"
                    }
                }
            }
            send_message(response)
        
        # Handle tools/list
        elif msg.get("method") == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": msg["id"],
                "result": {
                    "tools": [
                        {
                            "name": "test_tool",
                            "description": "A simple test tool",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        }
                    ]
                }
            }
            send_message(response)
        
        # Handle tools/call
        elif msg.get("method") == "tools/call":
            response = {
                "jsonrpc": "2.0",
                "id": msg["id"],
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": "Hello from MCP server!"
                        }
                    ]
                }
            }
            send_message(response)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""Test MCP wrapper for Claude Code compatibility"""

import subprocess
import json
import sys

def test_mcp_wrapper():
    """Test the MCP wrapper with typical Claude Code requests"""
    
    # Start the wrapper process
    proc = subprocess.Popen(
        ['/data/mcp_servers/mcp-orchestrator'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Test 1: Initialize
        request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "id": 1,
            "params": {
                "protocolVersion": "1.0.0",
                "clientInfo": {"name": "test", "version": "1.0"},
                "capabilities": {}
            }
        }
        
        proc.stdin.write(json.dumps(request) + '\n')
        proc.stdin.flush()
        
        # Read response
        response_line = proc.stdout.readline()
        if response_line:
            response = json.loads(response_line)
            print("Initialize response:", json.dumps(response, indent=2))
        
        # Test 2: List tools
        request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 2
        }
        
        proc.stdin.write(json.dumps(request) + '\n')
        proc.stdin.flush()
        
        # Wait a bit for response
        import time
        time.sleep(1)
        
        # Try to read response
        response_line = proc.stdout.readline()
        if response_line:
            response = json.loads(response_line)
            print("\nTools list response:", json.dumps(response, indent=2))
            
            # Show first few tools
            if 'result' in response and 'tools' in response['result']:
                print(f"\nFound {len(response['result']['tools'])} tools")
                for tool in response['result']['tools'][:5]:
                    print(f"  - {tool['name']}: {tool.get('description', 'No description')}")
        
    finally:
        # Clean up
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    test_mcp_wrapper()
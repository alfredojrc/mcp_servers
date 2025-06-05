#!/usr/bin/env python3
"""Test MCP connection using the SDK directly"""

import asyncio
import httpx
import json
import sys

async def test_sse_connection():
    """Test if we can connect to the SSE endpoint"""
    url = "http://localhost:8000/sse"
    
    async with httpx.AsyncClient() as client:
        print(f"Testing connection to {url}...")
        
        # Test 1: Basic connectivity
        try:
            response = await client.get(url.replace('/sse', '/health'), timeout=5.0)
            print(f"Health check: {response.status_code}")
        except Exception as e:
            print(f"Health check failed: {e}")
        
        # Test 2: SSE endpoint
        try:
            async with client.stream("GET", url, timeout=5.0) as response:
                print(f"SSE connection: {response.status_code}")
                
                # Read a few messages
                count = 0
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        print(f"Received: {line}")
                        count += 1
                        if count >= 3:
                            break
        except Exception as e:
            print(f"SSE connection failed: {e}")

async def test_stdio_script():
    """Test the STDIO script directly"""
    print("\nTesting STDIO script...")
    
    # Test initialization
    init_request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "1.0",
            "clientInfo": {"name": "test", "version": "1.0"},
            "capabilities": {}
        },
        "id": 1
    }
    
    cmd = f'echo \'{json.dumps(init_request)}\' | docker exec -i mcp_master python mcp_host_stdio_claude.py 2>&1'
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await proc.communicate()
    
    print("STDOUT:")
    for line in stdout.decode().split('\n'):
        if line.strip() and 'INFO' not in line:
            print(f"  {line}")
    
    if stderr:
        print("STDERR:")
        for line in stderr.decode().split('\n')[:10]:
            if line.strip():
                print(f"  {line}")

if __name__ == "__main__":
    asyncio.run(test_sse_connection())
    asyncio.run(test_stdio_script())
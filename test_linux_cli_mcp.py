#!/usr/bin/env python3
"""Test script for Linux CLI MCP service"""

import asyncio
import httpx
import json

async def test_linux_cli_mcp():
    """Test the Linux CLI MCP service capabilities"""
    base_url = "http://localhost:8001"
    
    # Test health endpoint
    async with httpx.AsyncClient() as client:
        print("Testing health endpoint...")
        response = await client.get(f"{base_url}/health")
        print(f"Health status: {response.status_code}")
        if response.status_code == 200:
            print(f"Health response: {response.json()}")
        
        # Test if it's using SSE transport
        print("\nTesting SSE endpoint...")
        headers = {"Content-Type": "application/json"}
        
        # Try different MCP methods
        methods = ["tools/list", "resources/list", "prompts/list"]
        
        for method in methods:
            print(f"\nTrying method: {method}")
            payload = {
                "jsonrpc": "2.0",
                "method": method,
                "id": 1
            }
            
            try:
                response = await client.post(
                    f"{base_url}/sse",
                    json=payload,
                    headers=headers,
                    timeout=5.0
                )
                print(f"Response status: {response.status_code}")
                if response.status_code == 200:
                    print(f"Response: {response.text[:200]}")
            except Exception as e:
                print(f"Error: {e}")
        
        # Try the messages endpoint
        print("\nTrying messages endpoint...")
        try:
            response = await client.post(
                f"{base_url}/messages",
                json=payload,
                headers=headers,
                timeout=5.0
            )
            print(f"Messages status: {response.status_code}")
        except Exception as e:
            print(f"Messages error: {e}")

if __name__ == "__main__":
    asyncio.run(test_linux_cli_mcp())
#!/usr/bin/env python3
"""Test the Secrets MCP service with personal KeePass database"""

import httpx
import json
import asyncio

async def test_keepass_via_mcp():
    """Test accessing KeePass through the MCP service"""
    base_url = "http://localhost:8013"
    
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        print("1. Testing health endpoint...")
        response = await client.get(f"{base_url}/health")
        print(f"   Health status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        
        print("\n2. Testing secrets.getSecret tool...")
        # The generic getSecret tool looks for "keepass/" prefix
        test_paths = [
            "keepass/Root/test",
            "keepass/Internet/github",
            "keepass/",
        ]
        
        for path in test_paths:
            print(f"\n   Trying path: {path}")
            try:
                # We need to make a proper MCP request
                # Since this is an SSE endpoint, we need to test differently
                print("   (SSE endpoint - would need proper MCP client)")
            except Exception as e:
                print(f"   Error: {e}")
        
        print("\n3. To properly test, we need to use the MCP client from inside a container...")
        print("   Or we can check what entries exist using docker exec")

if __name__ == "__main__":
    asyncio.run(test_keepass_via_mcp())
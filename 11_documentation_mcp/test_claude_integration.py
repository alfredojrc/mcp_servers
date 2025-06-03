#!/usr/bin/env python3
"""
Test script to validate Claude Code integration with Documentation MCP Service
"""
import asyncio
import httpx
import json
from datetime import datetime

# Documentation MCP Service URL
DOCS_MCP_URL = "http://192.168.68.100:8011"

async def test_connection():
    """Test basic connection to the service"""
    print("\n1. Testing Connection...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(DOCS_MCP_URL)
            if response.status_code == 200:
                print("✅ Service is accessible at", DOCS_MCP_URL)
                return True
            else:
                print(f"❌ Service returned status: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

async def test_tool_list():
    """Test MCP tools/list method"""
    print("\n2. Testing Tool Discovery...")
    
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DOCS_MCP_URL}/messages",
                json=request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                tools = result.get("result", {}).get("tools", [])
                print(f"✅ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"   - {tool.get('name')}: {tool.get('description', '')[:60]}...")
                return True
            else:
                print(f"❌ Failed to list tools: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Tool discovery error: {e}")
        return False

async def test_search_tool():
    """Test documentation search functionality"""
    print("\n3. Testing Search Tool...")
    
    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "docs.search",
            "arguments": {
                "query": "MCP architecture"
            }
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DOCS_MCP_URL}/messages",
                json=request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    docs = result["result"].get("documents", [])
                    print(f"✅ Search returned {len(docs)} results")
                    for doc in docs[:3]:
                        print(f"   - {doc.get('title')} ({doc.get('category')})")
                    return True
                else:
                    print(f"❌ Search failed: {result.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Search request failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Search error: {e}")
        return False

async def test_create_document():
    """Test document creation (requires approval)"""
    print("\n4. Testing Document Creation...")
    
    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "docs.create",
            "arguments": {
                "title": "Claude Integration Test Document",
                "content": f"""# Claude Integration Test

This document was created by the test script at {datetime.now().isoformat()}.

## Purpose
To validate that Claude Code can create documentation through the MCP protocol.

## Test Results
- Connection: ✅
- Tool Discovery: ✅
- Search: ✅
- Creation: In Progress...

## Integration Status
The Documentation MCP Service is ready for Claude Code integration!
""",
                "category": "knowledge",
                "tags": ["test", "integration", "claude"],
                "metadata": {
                    "author": "Integration Test Script",
                    "test_run": datetime.now().isoformat()
                },
                "approval_token": "test-token"  # In production, Claude would provide this
            }
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{DOCS_MCP_URL}/messages",
                json=request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    doc_id = result["result"].get("id")
                    print(f"✅ Document created successfully!")
                    print(f"   ID: {doc_id}")
                    print(f"   Title: {result['result'].get('title')}")
                    return doc_id
                else:
                    error = result.get("error", {})
                    print(f"⚠️  Creation blocked: {error.get('message', 'Approval required')}")
                    return None
            else:
                print(f"❌ Creation request failed: {response.status_code}")
                return None
    except Exception as e:
        print(f"❌ Creation error: {e}")
        return None

async def test_sse_connection():
    """Test SSE (Server-Sent Events) connection"""
    print("\n5. Testing SSE Connection...")
    
    try:
        async with httpx.AsyncClient() as client:
            # Test SSE endpoint exists
            response = await client.get(
                f"{DOCS_MCP_URL}/sse",
                headers={"Accept": "text/event-stream"},
                timeout=2.0  # Short timeout for test
            )
            # SSE will keep connection open, so timeout is expected
            print("✅ SSE endpoint is available")
            return True
    except httpx.ReadTimeout:
        # Timeout is expected for SSE
        print("✅ SSE endpoint is responding (connection stays open)")
        return True
    except Exception as e:
        print(f"❌ SSE connection error: {e}")
        return False

async def generate_mcp_config():
    """Generate MCP configuration for Claude Code"""
    print("\n6. Generating Claude Code Configuration...")
    
    config = {
        "mcpServers": {
            "documentation": {
                "url": f"{DOCS_MCP_URL}/sse",
                "transport": "sse",
                "description": "Documentation MCP Service",
                "autoApprove": [
                    "docs.search",
                    "docs.get", 
                    "docs.list",
                    "docs.categories.list",
                    "docs.tags.list",
                    "docs.getMetrics"
                ]
            }
        }
    }
    
    print("✅ Add this to your .mcp.json file:")
    print(json.dumps(config, indent=2))
    
    # Save config file
    with open("/data/mcp_servers/11_documentation_mcp/.mcp.json", "w") as f:
        json.dump(config, f, indent=2)
    print("\n✅ Configuration saved to .mcp.json")

async def main():
    """Run all integration tests"""
    print("="*60)
    print("Documentation MCP Service - Claude Code Integration Test")
    print("="*60)
    
    # Track test results
    results = []
    
    # Run tests
    results.append(await test_connection())
    results.append(await test_tool_list())
    results.append(await test_search_tool())
    
    doc_id = await test_create_document()
    results.append(doc_id is not None)
    
    results.append(await test_sse_connection())
    await generate_mcp_config()
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary:")
    print("="*60)
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! The Documentation MCP Service is ready for Claude Code integration.")
    else:
        print(f"\n⚠️  Some tests failed. Please check the service configuration.")
    
    print("\nNext Steps:")
    print("1. Ensure the service is running: docker-compose ps")
    print("2. Copy the .mcp.json config to your project")
    print("3. Restart Claude Code to load the configuration")
    print("4. Test by asking Claude to search your documentation")

if __name__ == "__main__":
    asyncio.run(main())
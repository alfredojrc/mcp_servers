#!/usr/bin/env python3
"""
Test end-to-end workflows through the MCP master orchestrator
"""
import asyncio
import httpx
import json
from datetime import datetime

MASTER_URL = "http://localhost:8080"

async def test_cmdb_query():
    """Test querying CMDB through master"""
    print("\n1. Testing CMDB Query...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Query CMDB for all assets
        request = {
            "tool": "cmdb.queryAssets",
            "arguments": {
                "filters": {},
                "fields": ["hostname", "ip_address", "services"]
            }
        }
        
        try:
            response = await client.post(f"{MASTER_URL}/execute", json=request)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ CMDB query successful!")
                print(f"   Found {len(result.get('assets', []))} assets")
                # Show first 3 assets
                for asset in result.get('assets', [])[:3]:
                    print(f"   - {asset.get('hostname')} ({asset.get('ip_address')})")
            else:
                print(f"❌ CMDB query failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ CMDB query error: {e}")

async def test_linux_command():
    """Test Linux command execution through master"""
    print("\n2. Testing Linux Command Execution...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Simple command to check system info
        request = {
            "tool": "linux.runLocalCommand",
            "arguments": {
                "command": "uname -a"
            }
        }
        
        try:
            response = await client.post(f"{MASTER_URL}/execute", json=request)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Linux command successful!")
                print(f"   Output: {result.get('stdout', '').strip()}")
            else:
                print(f"❌ Linux command failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Linux command error: {e}")

async def test_secrets_retrieval():
    """Test secrets retrieval through master"""
    print("\n3. Testing Secrets Retrieval...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Try to get a test secret
        request = {
            "tool": "secrets.get",
            "arguments": {
                "key": "test_secret"
            }
        }
        
        try:
            response = await client.post(f"{MASTER_URL}/execute", json=request)
            if response.status_code == 200:
                result = response.json()
                if "error" in result:
                    print(f"⚠️  Secrets service responded with: {result['error']}")
                else:
                    print(f"✅ Secrets retrieval successful!")
            else:
                print(f"❌ Secrets retrieval failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Secrets retrieval error: {e}")

async def test_workflow_chain():
    """Test a chained workflow"""
    print("\n4. Testing Chained Workflow...")
    print("   Scenario: Query CMDB → Get system info for first host")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Step 1: Query CMDB
        request1 = {
            "tool": "cmdb.queryAssets",
            "arguments": {
                "filters": {"os_type": "Docker"},
                "fields": ["hostname", "ip_address"]
            }
        }
        
        try:
            response1 = await client.post(f"{MASTER_URL}/execute", json=request1)
            if response1.status_code != 200:
                print(f"❌ CMDB query failed")
                return
            
            assets = response1.json().get('assets', [])
            if not assets:
                print(f"⚠️  No Docker assets found in CMDB")
                return
            
            first_host = assets[0]['hostname']
            print(f"   Found {len(assets)} Docker containers")
            print(f"   Checking first host: {first_host}")
            
            # Step 2: Get info about the host
            request2 = {
                "tool": "linux.runLocalCommand",
                "arguments": {
                    "command": f"docker ps --filter name={first_host} --format 'table {{{{.Names}}}}\\t{{{{.Status}}}}'"
                }
            }
            
            response2 = await client.post(f"{MASTER_URL}/execute", json=request2)
            if response2.status_code == 200:
                result = response2.json()
                print(f"✅ Workflow chain successful!")
                print(f"   Container status:\n{result.get('stdout', '').strip()}")
            else:
                print(f"❌ Container check failed")
                
        except Exception as e:
            print(f"❌ Workflow chain error: {e}")

async def test_freqtrade_knowledge():
    """Test Freqtrade knowledge base"""
    print("\n5. Testing Freqtrade Knowledge Base...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        request = {
            "tool": "trading.freqtrade.knowledge.backtestingBestPractices",
            "arguments": {}
        }
        
        try:
            response = await client.post(f"{MASTER_URL}/execute", json=request)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Freqtrade knowledge query successful!")
                # Show first 200 chars of response
                content = str(result.get('content', ''))[:200]
                print(f"   Response preview: {content}...")
            else:
                print(f"❌ Freqtrade query failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Freqtrade query error: {e}")

async def main():
    """Run all workflow tests"""
    print(f"\nMCP End-to-End Workflow Tests - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # First check if master is running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{MASTER_URL}/health")
            if response.status_code != 200:
                print("❌ Master orchestrator is not responding!")
                return
    except:
        print("❌ Cannot connect to master orchestrator at", MASTER_URL)
        return
    
    print("✅ Master orchestrator is running")
    
    # Run all tests
    await test_cmdb_query()
    await test_linux_command()
    await test_secrets_retrieval()
    await test_workflow_chain()
    await test_freqtrade_knowledge()
    
    print("\n" + "="*70)
    print("Workflow tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
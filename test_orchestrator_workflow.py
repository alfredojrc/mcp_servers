#!/usr/bin/env python3
"""Test script to execute workflow through orchestrator using SSE"""

import asyncio
import httpx
import json
import uuid
from typing import Optional, Dict, Any
import sys

SSE_BASE_URL = "http://localhost:8000"

class SSEClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session_id = None
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def connect(self):
        """Establish SSE connection"""
        response = await self.client.get(f"{self.base_url}/sse", follow_redirects=True)
        if response.status_code == 200:
            # Parse session ID from response
            for line in response.text.split('\n'):
                if line.startswith('data: ') and '/messages/?session_id=' in line:
                    self.session_id = line.split('session_id=')[1].strip()
                    print(f"Connected with session ID: {self.session_id}")
                    return True
        return False
        
    async def send_request(self, method: str, params: dict) -> Dict[str, Any]:
        """Send JSON-RPC request"""
        if not self.session_id:
            raise Exception("Not connected")
            
        request_id = str(uuid.uuid4())
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        # Send request
        response = await self.client.post(
            f"{self.base_url}/messages/?session_id={self.session_id}",
            json=request
        )
        
        if response.status_code != 202:
            raise Exception(f"Request failed: {response.status_code} - {response.text}")
            
        # Poll for response
        for _ in range(30):  # 30 second timeout
            await asyncio.sleep(1)
            
            # Check for response via SSE
            sse_response = await self.client.get(
                f"{self.base_url}/sse",
                headers={"Last-Event-ID": self.session_id}
            )
            
            for line in sse_response.text.split('\n'):
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        if data.get("id") == request_id:
                            return data
                    except:
                        pass
                        
        raise Exception("Request timeout")
        
    async def close(self):
        await self.client.aclose()

async def main():
    # The workflow to execute
    workflow = {
        "workflow_id": "TestLinuxUptime",
        "steps": [
            {
                "step_id": "run_uptime",
                "service": "os.linux",
                "tool": "cli.runCommand",
                "parameters": {
                    "command": "uptime",
                    "session_id": "default"
                }
            }
        ]
    }
    
    print("Connecting to orchestrator...")
    client = SSEClient(SSE_BASE_URL)
    
    try:
        if await client.connect():
            print("Executing workflow...")
            
            # Call the orchestrator tool
            result = await client.send_request(
                "tools/call",
                {
                    "name": "orchestrator_executeWorkflow",
                    "arguments": {
                        "workflow": workflow
                    }
                }
            )
            
            print("Workflow result:")
            print(json.dumps(result, indent=2))
        else:
            print("Failed to connect to orchestrator")
            
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
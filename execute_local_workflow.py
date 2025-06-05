#!/usr/bin/env python3
"""Execute a workflow through the MCP orchestrator to run a local command"""

import asyncio
import httpx
import json
import uuid

async def call_orchestrator_tool(tool_name, arguments):
    """Call a tool on the orchestrator using direct HTTP POST"""
    
    # Create the request payload
    request_payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": str(uuid.uuid4())
    }
    
    # Send request to orchestrator
    async with httpx.AsyncClient(timeout=30.0) as client:
        print(f"Calling orchestrator tool: {tool_name}")
        print(f"Arguments: {json.dumps(arguments, indent=2)}")
        
        # First establish SSE connection to get session
        async with client.stream("GET", "http://localhost:8000/sse") as sse_response:
            # Get session ID
            session_id = None
            async for line in sse_response.aiter_lines():
                if line.startswith("data: ") and "session_id=" in line:
                    endpoint = line[6:].strip()
                    session_id = endpoint.split("session_id=")[1]
                    break
            
            if not session_id:
                print("Failed to get session ID")
                return None
            
            # Send the request
            messages_url = f"http://localhost:8000/messages/?session_id={session_id}"
            
            # Send in background
            response_data = None
            async def send_and_receive():
                nonlocal response_data
                # Send request
                await client.post(
                    messages_url,
                    json=request_payload,
                    headers={"Content-Type": "application/json"}
                )
                
                # Read response from SSE
                timeout = 10
                start_time = asyncio.get_event_loop().time()
                
                async for line in sse_response.aiter_lines():
                    if asyncio.get_event_loop().time() - start_time > timeout:
                        break
                        
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            if data.get("id") == request_payload["id"]:
                                response_data = data
                                break
                        except:
                            pass
            
            # Execute send and receive
            try:
                await asyncio.wait_for(send_and_receive(), timeout=15)
            except asyncio.TimeoutError:
                print("Timeout waiting for response")
            
            return response_data

async def main():
    # Define workflow
    workflow_args = {
        "workflow_name": "check_local_disk_space",
        "steps": [
            {
                "name": "check_disk_usage",
                "service": "os.linux",
                "tool": "cli.runCommand",
                "params": {
                    "command": "df -h"
                }
            }
        ]
    }
    
    print("Executing workflow through orchestrator...")
    print("=" * 60)
    
    # Call orchestrator
    result = await call_orchestrator_tool("orchestrator_executeWorkflow", workflow_args)
    
    if result:
        print(f"\nOrchestrator Response:")
        print(json.dumps(result, indent=2))
        
        # Extract the actual command output if available
        if "result" in result and isinstance(result["result"], dict):
            workflow_result = result["result"]
            if "steps" in workflow_result:
                for step in workflow_result["steps"]:
                    if "result" in step and "stdout" in step["result"]:
                        print(f"\nCommand Output from step '{step.get('name', 'unknown')}':")
                        print(step["result"]["stdout"])
    else:
        print("No response received from orchestrator")

if __name__ == "__main__":
    asyncio.run(main())
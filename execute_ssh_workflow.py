#!/usr/bin/env python3
"""Execute SSH workflow through MCP orchestrator"""

import asyncio
import httpx
import json
import uuid

async def execute_workflow():
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Connect to SSE endpoint to get session
        print("Connecting to orchestrator SSE endpoint...")
        
        # Keep SSE connection open while we work
        async with client.stream("GET", "http://localhost:8000/sse") as sse_response:
            session_id = None
            messages_url = None
            
            # Read initial SSE messages to get session endpoint
            async for line in sse_response.aiter_lines():
                if line.startswith("event: endpoint"):
                    continue
                if line.startswith("data: "):
                    endpoint = line[6:].strip()
                    # Extract session ID from endpoint
                    if "session_id=" in endpoint:
                        session_id = endpoint.split("session_id=")[1]
                        messages_url = f"http://localhost:8000{endpoint}"
                        print(f"Got session ID: {session_id}")
                        print(f"Messages URL: {messages_url}")
                        break
            
            if not session_id:
                print("Failed to get session ID")
                return
            
            # Create the MCP request
            workflow_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "orchestrator_executeWorkflow",
                    "arguments": {
                        "workflow_name": "check_disk_space_aicrusher",
                        "steps": [
                            {
                                "name": "ssh_df_command",
                                "service": "os.linux",
                                "tool": "ssh",
                                "params": {
                                    "host": "aicrusher",
                                    "command": "df -h"
                                }
                            }
                        ]
                    }
                },
                "id": str(uuid.uuid4())
            }
            
            print(f"\nSending workflow request...")
            print(f"Request: {json.dumps(workflow_request, indent=2)}")
            
            # Send the request in a separate task while keeping SSE open
            async def send_request():
                response = await client.post(
                    messages_url,
                    json=workflow_request,
                    headers={"Content-Type": "application/json"}
                )
                print(f"\nResponse status: {response.status_code}")
                print(f"Response: {response.text}")
            
            # Create task to send request
            send_task = asyncio.create_task(send_request())
            
            # Continue reading SSE for response
            print("\nWaiting for SSE response...")
            timeout = 30  # 30 second timeout
            start_time = asyncio.get_event_loop().time()
            
            async for line in sse_response.aiter_lines():
                if asyncio.get_event_loop().time() - start_time > timeout:
                    print("Timeout waiting for response")
                    break
                    
                if line.startswith("data: "):
                    data_str = line[6:].strip()
                    if data_str and data_str != '':
                        try:
                            data = json.loads(data_str)
                            print(f"\nSSE Response: {json.dumps(data, indent=2)}")
                            
                            # Check if this is our response
                            if isinstance(data, dict) and data.get("id") == workflow_request["id"]:
                                print("\nReceived response to our workflow request!")
                                if "result" in data:
                                    print(f"Result: {json.dumps(data['result'], indent=2)}")
                                elif "error" in data:
                                    print(f"Error: {json.dumps(data['error'], indent=2)}")
                                break
                        except json.JSONDecodeError:
                            pass
                elif line.startswith(": ping"):
                    continue
                elif line.strip():
                    print(f"SSE: {line}")
            
            # Ensure send task completes
            await send_task

if __name__ == "__main__":
    asyncio.run(execute_workflow())
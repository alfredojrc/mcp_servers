#!/usr/bin/env python3
"""Simple test of orchestrator workflow execution"""

import httpx
import json
import uuid
import time

# First, establish SSE connection and get session ID
print("Getting session ID from orchestrator...")
session_response = httpx.get("http://localhost:8000/sse", timeout=5.0)
session_id = None

for line in session_response.text.split('\n'):
    if line.startswith("data: ") and "session_id=" in line:
        endpoint = line[6:].strip()
        session_id = endpoint.split("session_id=")[1]
        print(f"Got session ID: {session_id}")
        break

if not session_id:
    print("Failed to get session ID")
    exit(1)

# Create workflow request
workflow_request = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "orchestrator_executeWorkflow",
        "arguments": {
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
    },
    "id": str(uuid.uuid4())
}

# Send the request
messages_url = f"http://localhost:8000/messages/?session_id={session_id}"
print(f"\nSending workflow request to: {messages_url}")
print(f"Request ID: {workflow_request['id']}")

response = httpx.post(
    messages_url,
    json=workflow_request,
    headers={"Content-Type": "application/json"},
    timeout=10.0
)

print(f"Response status: {response.status_code}")
print(f"Response: {response.text}")

# Give it a moment to process
print("\nWaiting for workflow to complete...")
time.sleep(2)

print("\nCheck the orchestrator logs with:")
print(f"docker logs mcp_servers_00_master_mcp_1 --tail 100 | grep -A 10 '{workflow_request['id']}'")
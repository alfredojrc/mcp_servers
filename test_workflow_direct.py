#!/usr/bin/env python3
"""Direct test of workflow execution"""

import sys
import os
sys.path.insert(0, '/data/mcp_servers/00_master_mcp')

import asyncio
from mcp_host import orchestrator_workflow_engine

async def main():
    # The workflow matching your request
    workflow = {
        "workflow_id": "TestLinuxUptime",  
        "name": "Test Linux Uptime",  # Added name field as required by schema
        "steps": [
            {
                "service": "os.linux",
                "tool": "cli.runCommand",
                "params": {  # Changed from parameters to params as per schema
                    "command": "uptime",
                    "session_id": "default"
                }
            }
        ]
    }
    
    correlation_id = "test-" + str(os.getpid())
    
    print("Executing workflow...")
    try:
        result = await orchestrator_workflow_engine.execute_workflow(workflow, correlation_id)
        print("Workflow result:")
        print(result)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
MCP Host with STDIO transport for Claude Code compatibility
This implementation provides native STDIO support for Claude Desktop/Code
"""

import asyncio
import sys
import json
import logging
from typing import Dict, Any, Optional
from fastmcp import FastMCP
import httpx
import os
import uuid

# Configure logging to stderr to avoid interfering with STDIO protocol
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Service configuration - using SSE endpoints
SERVICES = {
    "os.linux": f"http://01_linux_cli_mcp:{os.getenv('MCP_PORT_01', '8001')}/sse",
    "infra.k8s": f"http://08_k8s_mcp:{os.getenv('MCP_PORT_08_K8S', '8008')}/sse",
    "docs": f"http://11_documentation_mcp:{os.getenv('MCP_PORT_11', '8011')}/sse",
    "cmdb": f"http://12_cmdb_mcp:{os.getenv('MCP_PORT_12', '8012')}/sse",
    "secrets": f"http://13_secrets_mcp:{os.getenv('MCP_PORT_13', '8013')}/sse",
    "trading.freqtrade.knowledge": f"http://15_freqtrade_mcp:{os.getenv('MCP_PORT_15', '8015')}/sse",
    "ai.models": f"http://16_ai_models_mcp:{os.getenv('MCP_PORT_16', '8016')}/sse",
    "crypto": f"http://17_crypto_trader_mcp:{os.getenv('MCP_PORT_17', '8017')}/sse",
    "vector": f"http://18_vector_db_mcp:{os.getenv('MCP_PORT_18', '8018')}/sse"
}

# Create the MCP server configuration for proxy
mcp_server_config = {"mcpServers": {}}
for namespace, url in SERVICES.items():
    # Remove /sse suffix for the proxy configuration
    base_url = url.replace("/sse", "")
    mcp_server_config["mcpServers"][namespace] = {"url": base_url}
    logger.info(f"Configuring proxy for namespace '{namespace}' to URL '{base_url}'")

# Initialize MCP as proxy with STDIO transport
mcp = FastMCP.as_proxy(
    mcp_server_config,
    name="mcp-orchestrator-stdio",
    instructions="Central MCP orchestrator with STDIO transport for Claude Code. Exposes system tools and proxies to downstream services. Also provides orchestrator.executeWorkflow.",
    transport="stdio"  # Use STDIO transport for Claude Code
)

# Define MCP_PORT for the HTTP host, same as in mcp_host.py
MCP_HTTP_PORT = int(os.getenv("MCP_PORT", 8000))

class MCPServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/') + "/mcp/" # Assumes /mcp endpoint
        self.client = httpx.AsyncClient()
        logger.info(f"MCPServiceClient (for STDIO WorkflowEngine) initialized to target {self.base_url}")

    async def call_tool(self, tool_name: str, params: dict, correlation_id: Optional[str]) -> dict:
        mcp_payload = {
            "mcp_version": "2.0", 
            "id": str(uuid.uuid4()),
            "type": "tool_call",
            "tool_name": tool_name,
            "parameters": params if params is not None else {}
        }
        if correlation_id:
             mcp_payload["correlation_id"] = correlation_id

        headers = {"Content-Type": "application/json"}
        try:
            logger.info(f"STDIO WorkflowEngine's MCPServiceClient calling tool: {tool_name} at {self.base_url} with params: {params}", 
                        extra={"props": {"target_tool": tool_name, "correlation_id": correlation_id, "mcp_id": mcp_payload['id']}})
            response = await self.client.post(self.base_url, json=mcp_payload, headers=headers)
            response.raise_for_status()
            result_data = response.json()
            logger.info(f"STDIO WorkflowEngine's MCPServiceClient received MCP response for {tool_name}: {result_data.get('type', 'N/A')}", 
                        extra={"props": {"target_tool": tool_name, "correlation_id": correlation_id, "mcp_id": mcp_payload['id']}})
            if result_data.get("type") == "tool_result":
                return {"status": "success", "result": result_data.get("result"), "id": result_data.get("id")}
            elif result_data.get("type") == "tool_error":
                 return {"status": "error", "error": result_data.get("error", {}).get("message", "Unknown tool error"), "details": result_data.get("error"), "id": result_data.get("id")}
            else:
                return {"status": "error", "error": "Unexpected MCP response type", "details": result_data, "id": result_data.get("id")}
        except httpx.HTTPStatusError as e:
            logger.error(f"STDIO WorkflowEngine: HTTP error calling tool {tool_name}: {e.response.status_code} - {e.response.text}", 
                         exc_info=True, extra={"props": {"target_tool": tool_name, "correlation_id": correlation_id}})
            try:
                error_details = e.response.json()
            except json.JSONDecodeError:
                error_details = {"error": e.response.text}
            return {"status": "error", "error": f"HTTP error: {e.response.status_code}", "details": error_details}
        except httpx.RequestError as e:
            logger.error(f"STDIO WorkflowEngine: Request error calling tool {tool_name}: {e}", 
                         exc_info=True, extra={"props": {"target_tool": tool_name, "correlation_id": correlation_id}})
            return {"status": "error", "error": f"Request error: {str(e)}"}
        except Exception as e:
            logger.error(f"STDIO WorkflowEngine: Unexpected error in MCPServiceClient calling tool {tool_name}: {e}", 
                         exc_info=True, extra={"props": {"target_tool": tool_name, "correlation_id": correlation_id}})
            return {"status": "error", "error": f"Unexpected error: {str(e)}"}

    async def close(self):
        await self.client.aclose()

class WorkflowEngine:
    def __init__(self, mcp_client: MCPServiceClient):
        self.mcp_client = mcp_client
        logger.info("WorkflowEngine (for STDIO host) initialized.")

    async def execute_workflow(self, workflow: dict, correlation_id: Optional[str]) -> dict:
        logger.info(f"STDIO WorkflowEngine: Executing workflow: {workflow.get('name')}", 
                    extra={"props": {"workflow_name": workflow.get('name'), "correlation_id": correlation_id}})
        results = []
        for i, step in enumerate(workflow.get('steps', [])):
            # Ensure step has service and tool keys
            if not all(k in step for k in ('service', 'tool')):
                logger.error(f"STDIO WorkflowEngine: Workflow '{workflow.get('name')}' step {i+1} is missing 'service' or 'tool' key.",
                             extra={"props": {"workflow_name": workflow.get('name'), "step_index": i, "correlation_id": correlation_id, "step_data": step }})
                error_result = {"status": "error", "error": f"Malformed step {i+1}: missing 'service' or 'tool'."}
                results.append({"step_name": "malformed_step", "result": error_result})
                return {"workflow_name": workflow.get('name'), "status": "failed", "step_failed_at": i, "reason": error_result, "results": results}

            proxied_tool_name = f"{step['service']}.{step['tool']}"
            logger.info(f"STDIO WorkflowEngine: Executing workflow step {i+1}/{len(workflow['steps'])}: {proxied_tool_name}", 
                        extra={"props": {"workflow_name": workflow.get('name'), "step_index": i, "target_tool": proxied_tool_name, "correlation_id": correlation_id}})
            
            step_params = step.get('params') # Ensure params is not None
            step_result = await self.mcp_client.call_tool(proxied_tool_name, step_params, correlation_id)
            results.append({"step_name": proxied_tool_name, "result": step_result})
            
            if isinstance(step_result, dict) and step_result.get("status") == "error":
                logger.error(f"STDIO WorkflowEngine: Workflow '{workflow.get('name')}' failed at step {i+1}: {proxied_tool_name}. Error: {step_result.get('error')}",
                             extra={"props": {"workflow_name": workflow.get('name'), "failed_step_index": i, "correlation_id": correlation_id, "error_details": step_result.get('details')}})
                return {"workflow_name": workflow.get('name'), "status": "failed", "step_failed_at": i, "reason": step_result, "results": results}
        
        logger.info(f"STDIO WorkflowEngine: Workflow '{workflow.get('name')}' completed successfully.",
                    extra={"props": {"workflow_name": workflow.get('name'), "correlation_id": correlation_id}})
        return {"workflow_name": workflow.get('name'), "status": "completed", "results": results}

# Initialize WorkflowEngine for the STDIO host
# This client will call back to the main mcp_host.py's HTTP/SSE endpoint
stdio_workflow_mcp_client = MCPServiceClient(base_url=f"http://localhost:{MCP_HTTP_PORT}")
stdio_workflow_engine = WorkflowEngine(mcp_client=stdio_workflow_mcp_client)

@mcp.tool("orchestrator.executeWorkflow")
async def execute_workflow_tool_stdio(workflow: dict) -> dict:
    """
    Executes a predefined workflow. The workflow definition specifies a sequence of 
    tool calls to be made to various MCP services. This tool is exposed via the STDIO 
    interface for Claude Code.
    The workflow itself is processed by making HTTP MCP calls to the main orchestrator
    HTTP/SSE endpoint, ensuring consistent tool resolution and proxying.
    """
    logger.info(f"STDIO execute_workflow_tool_stdio invoked for workflow: {workflow.get('name')}")
    # Attempt to get correlation_id from current task, fallback to new uuid
    current_task = asyncio.current_task()
    correlation_id = getattr(current_task, 'correlation_id', str(uuid.uuid4())) if current_task else str(uuid.uuid4())
    
    # It's crucial that stdio_workflow_engine's client is properly closed if the app has a shutdown phase.
    # For a continuously running script like this, client might be kept alive.
    # If FastMCP or this script has a graceful shutdown, stdio_workflow_mcp_client.close() should be called.
    return await stdio_workflow_engine.execute_workflow(workflow, correlation_id)

@mcp.tool("system.health")
async def check_health() -> Dict[str, Any]:
    """Check health status of all MCP services"""
    health_status = {
        "orchestrator": "healthy",
        "services": {}
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        for namespace, url in SERVICES.items():
            try:
                # Convert SSE URL to health check URL
                health_url = url.replace("/sse", "/health")
                response = await client.get(health_url)
                health_status["services"][namespace] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "code": response.status_code
                }
            except Exception as e:
                health_status["services"][namespace] = {
                    "status": "unreachable",
                    "error": str(e)
                }
    
    return health_status

@mcp.tool("system.listServices")
async def list_services() -> Dict[str, Any]:
    """List all available MCP services and their endpoints"""
    return {
        "services": [
            {"namespace": namespace, "endpoint": url, "transport": "sse"}
            for namespace, url in SERVICES.items()
        ]
    }

@mcp.resource("master://status")
def master_status_resource():
    """Get the current orchestrator status"""
    return {
        "status": "online",
        "service_name": mcp.name,
        "version": "1.0.0",
        "transport": "stdio",
        "proxied_namespaces": list(SERVICES.keys())
    }

def main():
    """Run the MCP server with STDIO transport"""
    logger.info("Starting MCP orchestrator with STDIO transport")
    logger.info(f"Proxying {len(SERVICES)} services. Workflow tool also available.")
    
    # Run the server - FastMCP will handle STDIO transport automatically
    mcp.run()

if __name__ == "__main__":
    main()
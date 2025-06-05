#!/usr/bin/env python3
import asyncio
import sys 
import json 
import logging
from typing import Dict, Any, Optional, List
from fastmcp import FastMCP
from fastmcp.tools import Tool
import httpx
import os
import uuid

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True 
)
logging.getLogger('fastmcp').setLevel(logging.DEBUG)
logging.getLogger('mcp').setLevel(logging.DEBUG)
logging.getLogger("httpx").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)

SERVICES = {
    "docs": f"http://01_documentation_mcp:{os.getenv('MCP_PORT_01', '8001')}/sse",
    "cmdb": f"http://02_cmdb_mcp:{os.getenv('MCP_PORT_02', '8002')}/sse",
    "secrets": f"http://03_secrets_mcp:{os.getenv('MCP_PORT_03', '8003')}/sse",
    "ai.models": f"http://04_ai_models_mcp:{os.getenv('MCP_PORT_04', '8004')}/sse",
    "vector": f"http://05_vector_db_mcp:{os.getenv('MCP_PORT_05', '8005')}/sse",
}

mcp_client_proxy_config = {"mcpServers": {}}
for namespace, url in SERVICES.items():
    base_url = url.replace("/sse", "") 
    mcp_client_proxy_config["mcpServers"][namespace] = {"url": base_url}
    logger.info(f"Main Orchestrator: Will proxy/call namespace '{namespace}' at base URL '{base_url}'")


class MCPServiceClient:
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0) 
        logger.info(f"Orchestrator's MCPServiceClient initialized to call downstream services.")

    async def call_tool(self, service_namespace: str, tool_name: str, params: dict, correlation_id: Optional[str]) -> dict:
        if service_namespace not in SERVICES:
            logger.error(f"Namespace '{service_namespace}' not found in configured SERVICES for tool '{service_namespace}.{tool_name}'.")
            return {"status": "error", "error": f"Service namespace '{service_namespace}' not configured."}

        target_url_from_config = SERVICES[service_namespace]
        post_url: str

        if service_namespace == "os.linux":
            # For os.linux, use the new /direct_tool_call endpoint
            base_url = target_url_from_config.replace("/sse", "") # Remove /sse suffix
            post_url = f"{base_url.rstrip('/')}/direct_tool_call"
            logger.info(f"Using direct tool call endpoint for '{service_namespace}': {post_url}")
        elif target_url_from_config.endswith("/sse"):
            # For other SSE services that might still use /messages/ (legacy or different setup)
            post_url = target_url_from_config.replace("/sse", "/messages/")
            logger.info(f"Adjusted POST URL for general SSE service '{service_namespace}' from {target_url_from_config} to: {post_url}")
        else:
            # Fallback for non-SSE configured services, assuming they want /messages/
            post_url = f"{target_url_from_config.rstrip('/')}/messages/"
            logger.info(f"Calculated POST URL for non-SSE configured service '{service_namespace}': {post_url}")
        
        full_tool_identifier = f"{service_namespace}.{tool_name}"

        # Prepare parameters and context for the MCP PDU
        current_params_for_tool = params if params is not None else {}
        
        mcp_pdu_context = {}
        if correlation_id:
            mcp_pdu_context["correlation_id"] = correlation_id

        # Construct the inner MCP PDU
        mcp_pdu = {
            "mcp_version": "2.0",
            "id": str(uuid.uuid4()),
            "type": "tool_call",
            "tool_name": full_tool_identifier,
            "parameters": current_params_for_tool,
            "context": mcp_pdu_context
        }

        # Wrap the MCP PDU in a JSON-RPC 2.0 request structure
        json_rpc_payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": mcp_pdu,
            "id": str(uuid.uuid4())
        }

        headers = {"Content-Type": "application/json", "Accept": "text/event-stream, application/json"} 
        
        logger.info(f"Orchestrator's MCPServiceClient calling tool: {full_tool_identifier} at {post_url} with JSON-RPC payload: {json.dumps(json_rpc_payload)}",
                    extra={"props": {"target_tool": full_tool_identifier, "correlation_id": correlation_id, "mcp_id": mcp_pdu['id'], "json_rpc_id": json_rpc_payload['id']}})
        try:
            response = await self.http_client.post(post_url, json=json_rpc_payload, headers=headers)
            response.raise_for_status() 
            
            result_data = response.json()
            
            # Handle JSON-RPC wrapped responses
            if "jsonrpc" in result_data and "result" in result_data:
                # Extract the actual MCP response from the JSON-RPC wrapper
                mcp_response = result_data["result"]
                logger.info(f"Orchestrator's MCPServiceClient received JSON-RPC wrapped MCP response for {full_tool_identifier}: {mcp_response.get('type', 'N/A')}",
                            extra={"props": {"target_tool": full_tool_identifier, "correlation_id": correlation_id, "mcp_id": mcp_pdu['id']}})
            else:
                # Direct MCP response (not wrapped)
                mcp_response = result_data
                logger.info(f"Orchestrator's MCPServiceClient received direct MCP response for {full_tool_identifier}: {mcp_response.get('type', 'N/A')}",
                            extra={"props": {"target_tool": full_tool_identifier, "correlation_id": correlation_id, "mcp_id": mcp_pdu['id']}})

            if mcp_response.get("type") == "tool_result":
                return {"status": "success", "result": mcp_response.get("result"), "id": mcp_response.get("id")}
            elif mcp_response.get("type") == "tool_error":
                return {"status": "error", "error": mcp_response.get("error", {}).get("message", "Unknown tool error from downstream service"), "details": mcp_response.get("error"), "id": mcp_response.get("id")}
            else:
                return {"status": "error", "error": "Unexpected MCP response type from downstream service", "details": result_data, "id": result_data.get("id")}

        except httpx.HTTPStatusError as e:
            error_text = e.response.text
            try:
                error_details = e.response.json()
            except json.JSONDecodeError:
                error_details = {"error_message": error_text}
            logger.error(f"Orchestrator MCPServiceClient: HTTP error calling {full_tool_identifier} on {post_url}: {e.response.status_code} - {error_text}",
                         exc_info=True, extra={"props": {"target_tool": full_tool_identifier, "correlation_id": correlation_id, "http_status": e.response.status_code }})
            return {"status": "error", "error": f"HTTP error: {e.response.status_code}", "details": error_details}
        except httpx.RequestError as e:
            logger.error(f"Orchestrator MCPServiceClient: Request error calling {full_tool_identifier} on {post_url}: {e}",
                         exc_info=True, extra={"props": {"target_tool": full_tool_identifier, "correlation_id": correlation_id}})
            return {"status": "error", "error": f"Request error: {str(e)}"}
        except Exception as e: 
            logger.error(f"Orchestrator MCPServiceClient: Unexpected error calling {full_tool_identifier} on {post_url}: {e}",
                         exc_info=True, extra={"props": {"target_tool": full_tool_identifier, "correlation_id": correlation_id}})
            return {"status": "error", "error": f"Unexpected error during tool call: {str(e)}"}

    async def close(self):
        await self.http_client.aclose()
        logger.info("Orchestrator's MCPServiceClient closed.")


class WorkflowEngine:
    def __init__(self, mcp_service_client: MCPServiceClient):
        self.mcp_client = mcp_service_client
        logger.info("Orchestrator's WorkflowEngine initialized.")

    async def execute_workflow(self, workflow: dict, correlation_id: Optional[str]) -> dict:
        workflow_name = workflow.get('name', 'Unnamed Workflow')
        logger.info(f"Orchestrator's WorkflowEngine: Executing workflow: {workflow_name}",
                    extra={"props": {"workflow_name": workflow_name, "correlation_id": correlation_id, "workflow_definition": workflow}})
        results = []
        workflow_steps = workflow.get('steps', [])

        for i, step in enumerate(workflow_steps):
            step_name_desc = step.get('name', f"Step {i+1}") 
            service_from_step = step.get('service')
            tool_from_step = step.get('tool')

            if not service_from_step or not tool_from_step:
                error_msg = f"Workflow '{workflow_name}' step {i+1} ('{step_name_desc}') is missing 'service' or 'tool' key."
                logger.error(error_msg, extra={"props": {"workflow_name": workflow_name, "step_index": i, "step_data": step, "correlation_id": correlation_id}})
                error_result = {"status": "error", "error": error_msg}
                results.append({"step_name": f"{service_from_step or 'unknown_service'}.{tool_from_step or 'unknown_tool'}", "description": step_name_desc, "result": error_result})
                return {"workflow_name": workflow_name, "status": "failed", "step_failed_at": i+1, "reason": error_result, "results": results, "correlation_id": correlation_id}

            step_params = step.get('params') 
            
            log_tool_identifier = f"{service_from_step}.{tool_from_step}"

            logger.info(f"Orchestrator's WorkflowEngine: Executing step {i+1}/{len(workflow_steps)} ('{step_name_desc}'): Call {log_tool_identifier}",
                        extra={"props": {"workflow_name": workflow_name, "step_index": i, "step_description": step_name_desc, "target_tool": log_tool_identifier, "correlation_id": correlation_id}})
            
            step_result = await self.mcp_client.call_tool(service_from_step, tool_from_step, step_params, correlation_id)
            results.append({"step_name": log_tool_identifier, "description": step_name_desc, "result": step_result})
            
            if isinstance(step_result, dict) and step_result.get("status") == "error":
                logger.error(f"Orchestrator's WorkflowEngine: Workflow '{workflow_name}' failed at step {i+1} ('{step_name_desc}'): {log_tool_identifier}. Error: {step_result.get('error')}",
                             extra={"props": {"workflow_name": workflow_name, "failed_step_index": i, "step_description": step_name_desc, "target_tool": log_tool_identifier, "error_details": step_result.get('details'), "correlation_id": correlation_id}})
                return {"workflow_name": workflow_name, "status": "failed", "step_failed_at": i+1, "reason": step_result, "results": results, "correlation_id": correlation_id}
        
        logger.info(f"Orchestrator's WorkflowEngine: Workflow '{workflow_name}' completed successfully.",
                    extra={"props": {"workflow_name": workflow_name, "correlation_id": correlation_id}})
        return {"workflow_name": workflow_name, "status": "completed", "results": results, "correlation_id": correlation_id}

orchestrator_mcp_service_client = MCPServiceClient() 
orchestrator_workflow_engine = WorkflowEngine(mcp_service_client=orchestrator_mcp_service_client)

# Define Tools
tools: List[Tool] = []

async def execute_workflow_implementation(workflow: dict, context: Optional[dict] = None) -> dict:
    correlation_id = context.get("correlation_id") if context else None
    logger.info(f"Orchestrator tool 'orchestrator_executeWorkflow' invoked for workflow: {workflow.get('name')}",
                extra={"props": {"workflow_name": workflow.get('name'), "correlation_id": correlation_id}})
    return await orchestrator_workflow_engine.execute_workflow(workflow, correlation_id)

tools.append(Tool(
    name="orchestrator_executeWorkflow",
    description="Executes a multi-step workflow by calling tools on configured MCP services.",
    fn=execute_workflow_implementation,
    parameters={
        "type": "object",
        "properties": {
            "workflow": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the workflow"},
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Optional descriptive name for the step"},
                                "service": {"type": "string", "description": "Namespace of the target MCP service (e.g., 'os_linux')"},
                                "tool": {"type": "string", "description": "Name of the tool to call on the service (e.g., 'listFiles')"},
                                "params": {"type": "object", "additionalProperties": True, "description": "Parameters to pass to the tool"}
                            },
                            "required": ["service", "tool", "params"]
                        }
                    }
                },
                "required": ["steps"]
            }
        },
        "required": ["workflow"],
        "additionalProperties": False
    },
    outputSchema={
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "Overall status of the workflow execution"},
            "step_results": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "step_name": {"type": "string"},
                        "status": {"type": "string"},
                        "result": {"type": "object", "additionalProperties": True}
                    },
                    "required": ["step_name", "status", "result"]
                }
            }
        },
        "required": ["status", "step_results"],
        "additionalProperties": False
    },
    inputSchema={
        "type": "object",
        "properties": {
            "workflow": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the workflow"},
                    "steps": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Optional descriptive name for the step"},
                                "service": {"type": "string", "description": "Namespace of the target MCP service (e.g., 'os_linux')"},
                                "tool": {"type": "string", "description": "Name of the tool to call on the service (e.g., 'listFiles')"},
                                "params": {"type": "object", "additionalProperties": True, "description": "Parameters to pass to the tool"}
                            },
                            "required": ["service", "tool", "params"]
                        }
                    }
                },
                "required": ["steps"]
            }
        },
        "required": ["workflow"],
        "additionalProperties": False
    }
))

async def check_system_health_implementation(context: Optional[dict] = None) -> Dict[str, Any]:
    health_status = {
        "orchestrator_status": "healthy",
        "orchestrator_name": "00_master_mcp", 
        "downstream_services": {}
    }
    correlation_id = context.get("correlation_id") if context else None

    async with httpx.AsyncClient(timeout=10.0) as client: 
        for namespace, service_sse_url in SERVICES.items():
            base_url = service_sse_url.replace("/sse", "")
            health_check_url = f"{base_url}/health" 

            logger.debug(f"Checking health of {namespace} at {health_check_url}", extra={"props": {"correlation_id": correlation_id}})
            try:
                response = await client.get(health_check_url) 
                if response.status_code == 200:
                    health_status["downstream_services"][namespace] = {"status": "healthy", "code": response.status_code, "details": response.json()}
                else:
                    health_status["downstream_services"][namespace] = {"status": "unhealthy", "code": response.status_code, "details": response.text}
            except Exception as e:
                logger.warning(f"Health check for {namespace} failed: {str(e)}", extra={"props": {"correlation_id": correlation_id}})
                health_status["downstream_services"][namespace] = {"status": "unreachable", "error": str(e)}
    return health_status

tools.append(Tool(
    name="system_health",
    description="Checks the health of the orchestrator and its downstream services.",
    fn=check_system_health_implementation,
    parameters={"type": "object", "properties": {}, "additionalProperties": False},
    inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
    outputSchema={
        "type": "object",
        "properties": {
            "orchestrator_status": {"type": "string"},
            "orchestrator_name": {"type": "string"},
            "downstream_services": {"type": "object"}
        }
    }
))

async def list_configured_services_implementation(context: Optional[dict] = None) -> Dict[str, Any]:
    correlation_id = context.get("correlation_id") if context else None
    logger.info(f"Orchestrator tool 'system_listServices' invoked.", extra={"props": {"correlation_id": correlation_id}})
    return {
        "configured_services": [{"namespace": ns, "url": url} for ns, url in SERVICES.items()]
    }

tools.append(Tool(
    name="system_listServices",
    description="Lists all downstream services configured in the orchestrator.",
    fn=list_configured_services_implementation,
    parameters={"type": "object", "properties": {}, "additionalProperties": False},
    inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
    outputSchema={
        "type": "object",
        "properties": {
            "configured_services": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "namespace": {"type": "string"},
                        "url": {"type": "string"}
                    }
                }
            }
        }
    }
))

# Define the lifespan context manager
async def lifespan(app: FastMCP):
    logger.info("Orchestrator: Lifespan event - startup. Initializing resources.")
    # MCPServiceClient is already initialized globally as orchestrator_mcp_service_client
    # If it needed async setup, it would be done here.
    yield
    logger.info("Orchestrator: Lifespan event - shutdown. Closing resources.")
    await orchestrator_mcp_service_client.close()

# Initialize FastMCP application
mcp_app = FastMCP(
    tools=tools,
    service_id="00_master_mcp_orchestrator", # Corrected parameter
    proxy_config=mcp_client_proxy_config    # Corrected parameter
)

# Assign the lifespan context manager to the app
mcp_app.lifespan_context = lifespan


if __name__ == "__main__":
    logger.info(f"Starting Master MCP Orchestrator (00_master_mcp) ...")
    try:
        mcp_app.run(transport="sse", host="0.0.0.0", port=8000, log_level="debug")
    except Exception as e:
        logger.error(f"Failed to start the Master MCP Orchestrator: {e}", exc_info=True)
        sys.exit(1)
import os
from fastmcp import FastMCP
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
import asyncio
import logging
import time
import json
from datetime import datetime as dt

import httpx
import uuid

class JSONFormatter(logging.Formatter):
    def __init__(self, service_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service_name = service_name

    def format(self, record):
        log_entry = {
            "timestamp": dt.now().isoformat(),
            "service": self.service_name,
            "level": record.levelname,
            "message": record.getMessage(),
            "correlation_id": getattr(record, 'correlation_id', None)
        }
        if hasattr(record, 'props') and record.props:
            log_entry['props'] = record.props
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        if record.stack_info:
            log_entry['stack_info'] = self.formatStack(record.stack_info)
        log_entry['logger_name'] = record.name
        log_entry['pathname'] = record.pathname
        log_entry['lineno'] = record.lineno
        return json.dumps(log_entry)

root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

SERVICE_NAME_FOR_LOGGING = "master-mcp-orchestrator"
json_formatter = JSONFormatter(SERVICE_NAME_FOR_LOGGING)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(json_formatter)
root_logger.addHandler(stream_handler)
root_logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())

logger = logging.getLogger(__name__)

MCP_PORT = int(os.getenv("MCP_PORT", 8000))

FOCUSED_DEFAULT_SERVERS = {
    "os.linux":       f"http://01_linux_cli_mcp:{os.getenv('MCP_PORT_01', '8001')}",
    "infra.k8s":      f"http://08_k8s_mcp:{os.getenv('MCP_PORT_08_K8S', '8008')}",
    "docs":           f"http://11_documentation_mcp:{os.getenv('MCP_PORT_11', '8011')}",
    "cmdb":           f"http://12_cmdb_mcp:{os.getenv('MCP_PORT_12', '8012')}",
    "secrets":        f"http://13_secrets_mcp:{os.getenv('MCP_PORT_13', '8013')}",
    "trading.freqtrade.knowledge": f"http://15_freqtrade_mcp:{os.getenv('MCP_PORT_15', '8015')}",
    "ai.models":      f"http://16_ai_models_mcp:{os.getenv('MCP_PORT_16', '8016')}"
}

mcp_server_config_payload = {"mcpServers": {}}
for namespace, url in FOCUSED_DEFAULT_SERVERS.items():
    mcp_server_config_payload["mcpServers"][namespace] = {"url": url}
    logger.info(f"Configuring proxy for namespace '{namespace}' to URL '{url}'")

mcp = FastMCP.as_proxy(
    mcp_server_config_payload, 
    name="Master Orchestrator Proxy - FastMCP Core", 
    instructions="Core FastMCP proxy for downstream services. Mounted at /mcp.",
    host="0.0.0.0",
    port=MCP_PORT,
    log_level="DEBUG"
)

@mcp.tool()
def master_hello_world(name="World"):
    return f"Hello from Master Orchestrator (tool via /mcp), {name}!"

@mcp.tool()
def master_add_numbers(a: int, b: int):
    """Adds two numbers together (Master Orchestrator version)."""
    return a + b

@mcp.resource("master://status")
def master_server_status_resource():
    """Get the current Master Orchestrator server status (resource)."""
    return {
        "status": "online",
        "service_name": mcp.name, 
        "port": MCP_PORT,
        "version": "1.0.0",
        "proxied_namespaces": list(FOCUSED_DEFAULT_SERVERS.keys())
    }
    
@mcp.tool("master.getServerInfo") 
def get_master_server_info():
    """Get information about the Master Orchestrator server itself."""
    return {
        "name": mcp.name,
        "version": "1.0.0",
        "port": MCP_PORT,
        "proxied_namespaces": list(FOCUSED_DEFAULT_SERVERS.keys())
    }

fastmcp_protocol_app = mcp.http_app()
logger.info(f"FastMCP ASGI app (fastmcp_protocol_app) created. Will be mounted at /mcp.")

async def root_health_endpoint(request):
    logger.debug("Accessed root /health endpoint")
    return JSONResponse({"status": "healthy", "service": SERVICE_NAME_FOR_LOGGING + " (Main Wrapper)", "timestamp": time.time()})

async def root_metrics_endpoint(request):
    logger.debug("Accessed root /metrics endpoint")
    return JSONResponse({
        "proxied_namespaces_count": len(FOCUSED_DEFAULT_SERVERS),
        "info": "Metrics for Master Orchestrator Proxy (Main Wrapper). Individual proxied services have their own metrics."
    })

async def homepage(request):
    return HTMLResponse("<h1>Master MCP Orchestrator</h1><p>MCP endpoint at /mcp. Health at /health. Metrics at /metrics.</p>")

main_app = Starlette(
    debug=True,
    routes=[
        Route("/", endpoint=homepage, methods=["GET"]),
        Route("/health", endpoint=root_health_endpoint, methods=["GET"]),
        Route("/metrics", endpoint=root_metrics_endpoint, methods=["GET"]),
        Mount("/mcp", app=fastmcp_protocol_app, name="fastmcp_core")
    ],
    on_startup=[lambda: logger.info(f"Main Starlette app (main_app) started. FastMCP app mounted at '/mcp'.")],
    on_shutdown=[lambda: logger.info("Main Starlette app (main_app) shutting down.")]
)

class MCPServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/') + "/mcp/"
        self.client = httpx.AsyncClient()
        logger.info(f"MCPServiceClient initialized to target {self.base_url}")

    async def call_tool(self, tool_name: str, params: dict, correlation_id: str) -> dict:
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
            logger.info(f"MCPServiceClient calling tool: {tool_name} at {self.base_url} with params: {params}", 
                        extra={"props": {"target_tool": tool_name, "correlation_id": correlation_id, "mcp_id": mcp_payload['id']}})
            response = await self.client.post(self.base_url, json=mcp_payload, headers=headers)
            response.raise_for_status()
            result_data = response.json()
            logger.info(f"MCPServiceClient received MCP response for {tool_name}: {result_data.get('type', 'N/A')}", 
                        extra={"props": {"target_tool": tool_name, "correlation_id": correlation_id, "mcp_id": mcp_payload['id']}})
            if result_data.get("type") == "tool_result":
                return {"status": "success", "result": result_data.get("result"), "id": result_data.get("id")}
            elif result_data.get("type") == "tool_error":
                 return {"status": "error", "error": result_data.get("error", {}).get("message", "Unknown tool error"), "details": result_data.get("error"), "id": result_data.get("id")}
            else:
                return {"status": "error", "error": "Unexpected MCP response type", "details": result_data, "id": result_data.get("id")}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling tool {tool_name}: {e.response.status_code} - {e.response.text}", 
                         exc_info=True, extra={"props": {"target_tool": tool_name, "correlation_id": correlation_id}})
            try:
                error_details = e.response.json()
            except json.JSONDecodeError:
                error_details = {"error": e.response.text}
            return {"status": "error", "error": f"HTTP error: {e.response.status_code}", "details": error_details}
        except httpx.RequestError as e:
            logger.error(f"Request error calling tool {tool_name}: {e}", 
                         exc_info=True, extra={"props": {"target_tool": tool_name, "correlation_id": correlation_id}})
            return {"status": "error", "error": f"Request error: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error in MCPServiceClient calling tool {tool_name}: {e}", 
                         exc_info=True, extra={"props": {"target_tool": tool_name, "correlation_id": correlation_id}})
            return {"status": "error", "error": f"Unexpected error: {str(e)}"}

    async def close(self):
        await self.client.aclose()

class WorkflowEngine:
    def __init__(self, mcp_client: MCPServiceClient):
        self.mcp_client = mcp_client
        logger.info("WorkflowEngine initialized.")

    async def execute_workflow(self, workflow: dict, correlation_id: str) -> dict:
        logger.info(f"Executing workflow: {workflow['name']}", 
                    extra={"props": {"workflow_name": workflow['name'], "correlation_id": correlation_id}})
        results = []
        for i, step in enumerate(workflow['steps']):
            proxied_tool_name = f"{step['service']}.{step['tool']}"
            logger.info(f"Executing workflow step {i+1}/{len(workflow['steps'])}: {proxied_tool_name}", 
                        extra={"props": {"workflow_name": workflow['name'], "step_index": i, "target_tool": proxied_tool_name, "correlation_id": correlation_id}})
            step_result = await self.mcp_client.call_tool(proxied_tool_name, step['params'], correlation_id)
            results.append({"step_name": f"{step['service']}.{step['tool']}", "result": step_result})
            if isinstance(step_result, dict) and step_result.get("status") == "error":
                logger.error(f"Workflow '{workflow['name']}' failed at step {i+1}: {proxied_tool_name}. Error: {step_result.get('error')}",
                             extra={"props": {"workflow_name": workflow['name'], "failed_step_index": i, "correlation_id": correlation_id, "error_details": step_result.get('details')}})
                return {"workflow_name": workflow['name'], "status": "failed", "step_failed_at": i, "reason": step_result, "results": results}
        logger.info(f"Workflow '{workflow['name']}' completed successfully.",
                    extra={"props": {"workflow_name": workflow['name'], "correlation_id": correlation_id}})
        return {"workflow_name": workflow['name'], "status": "completed", "results": results}

class EnhancedMCPHost:
    def __init__(self, mcp_instance: FastMCP, master_server_base_url: str):
        self.mcp = mcp_instance
        self.master_client = MCPServiceClient(base_url=master_server_base_url)
        self.workflow_engine = WorkflowEngine(self.master_client)
        @self.mcp.tool("orchestrator.executeWorkflow")
        async def execute_workflow_tool(workflow: dict) -> dict:
            logger.info(f"execute_workflow_tool invoked for workflow: {workflow.get('name')}")
            current_correlation_id = getattr(asyncio.Task.current_task(), 'correlation_id', str(uuid.uuid4())) if asyncio.Task.current_task() else str(uuid.uuid4())
            return await self.workflow_engine.execute_workflow(workflow, current_correlation_id)
        logger.info("EnhancedMCPHost initialized and workflow tool registered.")

master_base_url_for_client = f"http://localhost:{MCP_PORT}" 
enhanced_host = EnhancedMCPHost(mcp_instance=mcp, master_server_base_url=master_base_url_for_client)

async def run_main_app_directly():
    logger.info(f"Starting Main Starlette App (main_app) on port {MCP_PORT}...")
    config = uvicorn.Config(main_app, host="0.0.0.0", port=MCP_PORT, log_level=root_logger.level)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(run_main_app_directly()) 
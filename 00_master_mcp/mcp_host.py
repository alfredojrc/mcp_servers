import os
from fastmcp import FastMCP
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
import asyncio
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import logging
import time # Added for health check
import json
from datetime import datetime as dt # Alias to avoid conflict

# --- Add these imports ---
import httpx # For making HTTP requests in MCPServiceClient
import uuid  # For generating unique JSON-RPC IDs

# --- JSON Formatter Class ---
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
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        if record.stack_info:
            log_entry['stack_info'] = self.formatStack(record.stack_info)
        # Add other standard fields if needed
        log_entry['logger_name'] = record.name
        log_entry['pathname'] = record.pathname
        log_entry['lineno'] = record.lineno
        return json.dumps(log_entry)

# --- Logging Setup ---
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

SERVICE_NAME_FOR_LOGGING = "Master Orchestrator Proxy"
json_formatter = JSONFormatter(SERVICE_NAME_FOR_LOGGING)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(json_formatter)
root_logger.addHandler(stream_handler)
root_logger.setLevel(logging.DEBUG) # Keep DEBUG level as was previously set for this service

logger = logging.getLogger(__name__) # Module-specific logger, inherits root config

# Get port from environment variable or use 8000 as default
MCP_PORT = int(os.getenv("MCP_PORT", 8000))

# --- Define DEFAULT_SERVERS for proxying ---
DEFAULT_SERVERS = {
    "os.linux":       f"http://01_linux_cli_mcp:{os.getenv('MCP_PORT_01', '5001')}",
    # "os.windows":     f"http://02_windows_mcp:{os.getenv('MCP_PORT_02', '8002')}", # Not yet implemented
    "cloud.azure":    f"http://03_azure_mcp:{os.getenv('MCP_PORT_03', '8003')}", # README only, no server
    # "cloud.gcloud":   f"http://04_google_cloud_mcp:{os.getenv('MCP_PORT_04', '8004')}", # README only
    # "infra.vmware":   f"http://05_vmware_mcp:{os.getenv('MCP_PORT_05', '8005')}", # README only
    # "web.search":     f"http://06_web_search_mcp:{os.getenv('MCP_PORT_06', '8006')}", # README only
    # "web.browse":     f"http://07_web_browsing_mcp:{os.getenv('MCP_PORT_07', '8007')}", # README only
    "infra.k8s":      f"http://08_k8s_mcp:{os.getenv('MCP_PORT_08', '5008')}", # Note: k8s main.py is on 5001 in its Dockerfile, roadmap implies 8008. Using 5008 as per README pattern.
    # "workflows.n8n":  f"http://09_n8n_mcp:{os.getenv('MCP_PORT_09', '8009')}", # README only
    # "os.macos":       f"http://10_macos_mcp:{os.getenv('MCP_PORT_10', '8010')}", # README only
    # "trading.freq":   f"http://11_freqtrade_mcp:{os.getenv('MCP_PORT_11', '8011')}", # README only
    "cmdb":           f"http://12_cmdb_mcp:{os.getenv('MCP_PORT_12', '5012')}",
    "secrets":        f"http://13_secrets_mcp:{os.getenv('MCP_PORT_13', '8013')}",
    # "aider": f"http://14_aider_mcp:{os.getenv('MCP_PORT_14', '8014')}" # Dockerfile only
}
# Filter out services that are not expected to be running (e.g. README only)
# For now, let's try to connect to all defined in the original DEFAULT_SERVERS from README
# and let it fail gracefully if a service is down. The proxy should still start.
# However, for a cleaner setup, only include active services.
# The provided DEFAULT_SERVERS from README is extensive, let's use a focused list for now.
# Based on services we've touched (linux, k8s, secrets, cmdb)

FOCUSED_DEFAULT_SERVERS = {
    "os.linux":       f"http://01_linux_cli_mcp:{os.getenv('MCP_PORT_01', '8001')}",
    "infra.k8s":      f"http://08_k8s_mcp:{os.getenv('MCP_PORT_08_K8S', '8008')}", # k8s in its main.py uses WEBCONTROL_PORT or 5001, Docker Compose now uses 8008
    "cmdb":           f"http://12_cmdb_mcp:{os.getenv('MCP_PORT_12', '8012')}",
    "secrets":        f"http://13_secrets_mcp:{os.getenv('MCP_PORT_13', '8013')}",
    "trading.freqtrade": f"http://15_freqtrade_mcp:{os.getenv('MCP_PORT_15', '8015')}" # Added Freqtrade MCP
}


mcp_server_config_payload = {"mcpServers": {}}
for namespace, url in FOCUSED_DEFAULT_SERVERS.items():
    # FastMCP.as_proxy expects a URL. The transport might be auto-detected.
    # Based on gofastmcp.com docs, Streamable HTTP is common for remote.
    # Let's assume client can auto-negotiate or defaults appropriately.
    # If explicit transport is needed: "transport": "streamable-http" or "sse"
    mcp_server_config_payload["mcpServers"][namespace] = {"url": url}
    logger.info(f"Configuring proxy for namespace '{namespace}' to URL '{url}'")


# Create the master orchestrator server using FastMCP.as_proxy
# This mcp instance will act as a proxy AND can have its own tools.
mcp = FastMCP.as_proxy(
    mcp_server_config_payload, # This is the config for backend servers to proxy
    name="Master Orchestrator Proxy", 
    instructions="MCP Host server that coordinates MCP services via proxying, and provides its own tools.",
    host="0.0.0.0",
    port=MCP_PORT
    # Other FastMCP constructor args can go here if needed, like lifespan, tags etc.
)

# Enable debugging
mcp.settings.debug = True

# Create simple MCP tool functions
@mcp.tool()
def master_hello_world(name="World"):
    """A simple hello world tool from the Master Orchestrator itself."""
    return f"Hello from Master Orchestrator, {name}!"

@mcp.tool()
def master_add_numbers(a: int, b: int):
    """Adds two numbers together (Master Orchestrator version)."""
    return a + b

@mcp.resource("master://status")
def master_server_status_resource():
    """Get the current Master Orchestrator server status (resource)."""
    return {
        "status": "online",
        "service_name": mcp.name, # Accessing the name of the mcp instance
        "port": MCP_PORT,
        "version": "1.0.0",
        "proxied_namespaces": list(FOCUSED_DEFAULT_SERVERS.keys())
    }
    
# The original get_server_info tool, namespaced to avoid conflict if proxied services have same name
@mcp.tool("master.getServerInfo") 
def get_master_server_info():
    """Get information about the Master Orchestrator server itself."""
    return {
        "name": mcp.name,
        "version": "1.0.0",
        "port": MCP_PORT,
        "proxied_namespaces": list(FOCUSED_DEFAULT_SERVERS.keys())
    }
    
# Health Check Endpoint for the proxy server itself
async def health_check(request):
    # service_name = mcp.name if hasattr(mcp, 'name') else "Master Orchestrator Proxy"
    # Using the logger's service name for consistency
    return JSONResponse({"status": "healthy", "service": SERVICE_NAME_FOR_LOGGING, "timestamp": time.time()})

# Create a middleware for request logging
class LoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            logger.debug(f"Request: {scope['method']} {scope['path']}")
            
            # Modified send to log responses
            async def send_with_logging(message):
                if message["type"] == "http.response.start":
                    logger.debug(f"Response status: {message['status']}")
                await send(message)
            
            await self.app(scope, receive, send_with_logging)
        else:
            await self.app(scope, receive, send)

# Get the MCP app
mcp_app = mcp.sse_app()

# Remove the Starlette app wrapper
# app = Starlette(...)

# --- Health Check Endpoint ---
async def health_check(request): # Starlette request argument
    service_name = mcp.name if hasattr(mcp, 'name') else "Master Orchestrator" # Fallback for safety
    return JSONResponse({"status": "healthy", "service": service_name, "timestamp": time.time()})

# --- Placeholder for Enhanced Orchestrator Components ---

class MCPServiceClient:
    def __init__(self, service_name: str, service_url: str):
        self.service_name = service_name
        self.service_url = service_url.rstrip('/') # Ensure no trailing slash for consistency
        self.http_client = httpx.AsyncClient(timeout=30.0) # Increased timeout for potentially long tool calls
        logger.info(f"MCPServiceClient initialized for {service_name} at {self.service_url}")

    async def call_tool(self, tool_name: str, params: dict) -> dict:
        request_id = str(uuid.uuid4())
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "tool": tool_name,
                "params": params
            },
            "id": request_id
        }
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "MCPServiceClient/1.0"
        }
        
        effective_url = f"{self.service_url}/" # POST to the root of the MCP server
        
        logger.debug(f"MCPServiceClient: Calling tool {tool_name} on {effective_url} with params {params}, request_id: {request_id}")
        
        try:
            response = await self.http_client.post(effective_url, json=payload, headers=headers)
            response.raise_for_status() # Raise an exception for 4xx/5xx status codes
            
            response_data = response.json()
            logger.debug(f"MCPServiceClient: Response for {tool_name}, request_id {request_id}: {response_data}")

            if response_data.get("id") != request_id:
                logger.error(f"MCPServiceClient: JSON-RPC ID mismatch for {tool_name}. Expected {request_id}, got {response_data.get('id')}")
                return {"error": {"code": -32603, "message": "Internal error: JSON-RPC ID mismatch"}}

            if "error" in response_data:
                logger.error(f"MCPServiceClient: Error calling tool {tool_name}: {response_data['error']}")
                return {"error": response_data["error"]}
            
            return {"result": response_data.get("result")}
            
        except httpx.HTTPStatusError as e:
            logger.error(f"MCPServiceClient: HTTP error calling tool {tool_name} on {effective_url}: {e.response.status_code} - {e.response.text}", exc_info=True)
            return {"error": {"code": -32000, "message": f"HTTP error: {e.response.status_code}", "data": e.response.text}}
        except httpx.RequestError as e:
            logger.error(f"MCPServiceClient: Request error calling tool {tool_name} on {effective_url}: {e}", exc_info=True)
            return {"error": {"code": -32001, "message": f"Request error: {str(e)}"}}
        except json.JSONDecodeError as e:
            logger.error(f"MCPServiceClient: JSON decode error for tool {tool_name} response from {effective_url}: {e}", exc_info=True)
            return {"error": {"code": -32700, "message": "Parse error: Invalid JSON response"}}

class WorkflowEngine:
    def __init__(self, master_mcp_client: MCPServiceClient): # Modified parameter
        self.master_mcp_client = master_mcp_client # Modified attribute name
        logger.info("WorkflowEngine initialized with Master MCP Client.")

    async def execute_workflow(self, workflow_definition: dict) -> dict:
        workflow_name = workflow_definition.get('name', 'Unnamed Workflow')
        logger.info(f"WorkflowEngine: Starting execution of workflow: {workflow_name}")
        full_results = {"workflow_name": workflow_name, "status": "pending", "steps": []}
        
        has_errors = False
        for i, step_def in enumerate(workflow_definition.get("steps", [])):
            step_number = i + 1
            service_namespace = step_def.get("service")
            original_tool_name = step_def.get("tool")
            params = step_def.get("params", {})

            if not service_namespace or not original_tool_name:
                logger.error(f"Workflow '{workflow_name}' Step {step_number}: Invalid step definition, missing 'service' or 'tool'. Step: {step_def}")
                full_results["steps"].append({
                    "step": step_number, "service": service_namespace, "tool": original_tool_name,
                    "status": "error", "error": {"message": "Invalid step definition: missing 'service' or 'tool'."}
                })
                has_errors = True
                break 

            # Construct the fully qualified tool name for the master proxy
            proxied_tool_name = f"{service_namespace}.{original_tool_name}"
            
            logger.info(f"Workflow '{workflow_name}' Step {step_number}: Executing {proxied_tool_name} with params {params}")
            
            try:
                # Use the master_mcp_client to call the proxied tool
                tool_response = await self.master_mcp_client.call_tool(proxied_tool_name, params)
                
                if tool_response and "error" in tool_response and tool_response["error"] is not None: # Check if error field exists and is not None
                    logger.error(f"Workflow '{workflow_name}' Step {step_number} ({proxied_tool_name}): Tool call failed: {tool_response['error']}")
                    full_results["steps"].append({
                        "step": step_number, "service": service_namespace, "tool": original_tool_name,
                        "status": "error", "error": tool_response["error"], "params": params
                    })
                    has_errors = True
                    # Decide on error handling: break, continue, or conditional logic (not implemented yet)
                    break # Stop workflow on first error for now
                else:
                    logger.info(f"Workflow '{workflow_name}' Step {step_number} ({proxied_tool_name}): Succeeded.")
                    full_results["steps"].append({
                        "step": step_number, "service": service_namespace, "tool": original_tool_name,
                        "status": "success", "result": tool_response.get("result"), "params": params
                    })

            except Exception as e:
                logger.error(f"Workflow '{workflow_name}' Step {step_number} ({proxied_tool_name}): Exception during tool call: {e}", exc_info=True)
                full_results["steps"].append({
                    "step": step_number, "service": service_namespace, "tool": original_tool_name,
                    "status": "error", "error": {"message": str(e)}, "params": params
                })
                has_errors = True
                break # Stop workflow on first error

        if has_errors:
            full_results["status"] = "failed"
        else:
            full_results["status"] = "completed"
            
        logger.info(f"WorkflowEngine: Finished execution of workflow: {workflow_name}, Status: {full_results['status']}")
        return full_results

class EnhancedMCPHost:
    def __init__(self, mcp_instance: FastMCP, master_server_base_url: str): # Modified parameter
        self.mcp = mcp_instance
        # self.proxied_servers = proxied_servers_config # This is not directly used anymore if client talks to master
        
        self.master_client = MCPServiceClient(
            service_name="master_orchestrator_internal_client", 
            service_url=master_server_base_url
        )
        
        self.workflow_engine = WorkflowEngine(self.master_client) # Pass the single master client
        
        # Register workflow execution tool with the main mcp instance
        @self.mcp.tool("orchestrator.executeWorkflow")
        async def execute_workflow_tool(workflow: dict) -> dict:
            """
            Executes a predefined workflow consisting of multiple tool calls across different services.
            The workflow parameter should be a dictionary defining the workflow name and steps.
            Example:
            {
                'name': 'deploy_application',
                'description': 'Deploy application to Kubernetes',
                'steps': [
                    {'service': 'secrets', 'tool': 'getSecret', 'params': {'secretName': 'docker-registry'}},
                    {'service': 'infra.k8s', 'tool': 'apply_manifest', 'params': {'namespace': 'production', 'yaml_manifest': '...'}},
                    {'service': 'os.linux', 'tool': 'runCommand', 'params': {'command': 'curl health-check'}}
                ]
            }
            """
            logger.info(f"execute_workflow_tool invoked for workflow: {workflow.get('name')}")
            return await self.workflow_engine.execute_workflow(workflow)

        logger.info("EnhancedMCPHost initialized and workflow tool registered.")

# --- Initialize Enhanced Host capabilities ---
# We use FOCUSED_DEFAULT_SERVERS as the config for proxied servers.
# The master_server_base_url should point to where the 'mcp' instance is served.
master_base_url = f"http://localhost:{MCP_PORT}" # Assuming localhost for internal calls
enhanced_host = EnhancedMCPHost(mcp_instance=mcp, master_server_base_url=master_base_url)

if __name__ == "__main__":
    print(f"Starting MCP Host (Proxy) directly on port {MCP_PORT}...")

    # Add the health check route to mcp_app (which is a Starlette app)
    health_route_exists = any(r.path == "/health" for r in getattr(mcp_app, 'routes', []))
    if not health_route_exists:
        if not hasattr(mcp_app, 'routes') or not isinstance(mcp_app.routes, list):
            logger.warning("Starlette mcp_app.routes is not a list, cannot append health route directly.")
            if hasattr(mcp_app, 'router') and hasattr(mcp_app.router, 'routes') and isinstance(mcp_app.router.routes, list):
                 mcp_app.router.routes.append(Route("/health", health_check))
                 logger.info("Health check route added to mcp_app.router.routes.")
            elif hasattr(mcp_app, 'routes') and isinstance(mcp_app.routes, list): 
                 mcp_app.routes.append(Route("/health", health_check))
                 logger.info("Health check route added to mcp_app.routes.")
            else:
                logger.error("Cannot add health check route: mcp_app.routes or mcp_app.router.routes list not found or not a list.")
        else: 
            mcp_app.routes.append(Route("/health", health_check))
            logger.info("Health check route added to mcp_app.routes.")
    else:
        logger.info("Health check route already exists for mcp_app.")

    # Run the server with the mcp_app directly (now including /health)
    uvicorn_config = uvicorn.Config(app=mcp_app, host="0.0.0.0", port=MCP_PORT, log_level="info")
    server = uvicorn.Server(uvicorn_config)
    server.run() 
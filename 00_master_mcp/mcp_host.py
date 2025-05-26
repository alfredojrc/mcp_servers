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
    "os.linux":       f"http://01_linux_cli_mcp:{os.getenv('MCP_PORT_01', '5001')}",
    "infra.k8s":      f"http://08_k8s_mcp:{os.getenv('MCP_PORT_08_K8S', '5001')}", # k8s in its main.py uses WEBCONTROL_PORT or 5001, Docker Compose uses 5001
    "cmdb":           f"http://12_cmdb_mcp:{os.getenv('MCP_PORT_12', '5012')}",
    "secrets":        f"http://13_secrets_mcp:{os.getenv('MCP_PORT_13', '8013')}",
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
import os
import logging
from mcp.host.fastmcp import FastMCPHost
# from mcp_agent import AgentGraph # Keep commented out unless needed immediately for complex agent logic

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define downstream servers with hierarchical namespaces
# URLs use Docker Compose service names and their internal ports
# These mirror the structure defined in 00_master_mcp/README.md
DEFAULT_SERVERS = {
    "os.linux":       "http://01_linux_cli_mcp:5001",
    "os.windows":     "http://02_windows_mcp:5002",
    "cloud.azure":    "http://03_azure_mcp:5003",
    "cloud.gcloud":   "http://04_google_cloud_mcp:5004",
    "infra.vmware":   "http://05_vmware_mcp:5005",
    "web.search":     "http://06_web_search_mcp:5006",
    "web.browse":     "http://07_web_browsing_mcp:5007",
    "infra.k8s":      "http://08_k8s_mcp:5008",
    "workflows.n8n":  "http://09_n8n_mcp:5009",
    "os.macos":       "http://10_macos_mcp:5010",
    "trading.freq":   "http://11_freqtrade_mcp:5011",
}

# Allow overriding individual server URLs via environment variables if needed
# Example: export MCP_SERVER_URL_OS_LINUX="http://custom_linux_host:5001"
servers_to_register = {}
for ns, default_url in DEFAULT_SERVERS.items():
    env_var_name = f"MCP_SERVER_URL_{ns.upper().replace('.', '_')}"
    url = os.getenv(env_var_name, default_url)
    servers_to_register[ns] = url

# Get host port from environment variable or use default
MCP_HOST_PORT = int(os.getenv("MCP_PORT", 5000))

host = None
try:
    logger.info(f"Initializing FastMCPHost on port {MCP_HOST_PORT}")
    # Name should ideally be DNS-compatible if this host were discoverable
    host = FastMCPHost(name="master-mcp-host", port=MCP_HOST_PORT)

    # a_graph = AgentGraph(host) # Instantiate if using mcp-agent features

    logger.info("Registering downstream MCP servers:")
    for namespace, url in servers_to_register.items():
        logger.info(f"  - Namespace: {namespace:<15} URL: {url}")
        # Register each server with its full hierarchical namespace
        host.add_server(namespace=namespace, url=url)

except Exception as e:
    logger.error(f"Fatal error during MCP Host initialization: {e}", exc_info=True)
    # Optionally, exit if initialization fails critically
    # exit(1)

if __name__ == "__main__":
    if host:
        try:
            logger.info(f"Starting MCP Host server listener on port {MCP_HOST_PORT}...")
            # This call likely blocks and runs the ASGI server (e.g., uvicorn)
            host.run()
        except Exception as e:
             logger.error(f"MCP Host failed during runtime: {e}", exc_info=True)
             exit(1)
    else:
        logger.error("MCP Host object was not initialized successfully. Exiting.")
        exit(1) 
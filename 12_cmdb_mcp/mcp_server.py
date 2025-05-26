import os
import logging
from typing import Optional, List, Dict, Any

from mcp.server.fastmcp import FastMCP

# Add these imports
import time
from starlette.routing import Route
from starlette.responses import JSONResponse
import uvicorn

# Add these imports for JSON logging
import json
from datetime import datetime as dt # Alias to avoid conflict

# Optional imports based on chosen backends
try:
    import pandas as pd
except ImportError:
    pd = None

# try:
#     import requests
# except ImportError:
#     requests = None

# try:
#     import pysnow
# except ImportError:
#     pysnow = None

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

SERVICE_NAME_FOR_LOGGING = "cmdb-service"
json_formatter = JSONFormatter(SERVICE_NAME_FOR_LOGGING)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(json_formatter)
root_logger.addHandler(stream_handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__) # Module-specific logger, inherits root config

# --- Configuration ---
MCP_PORT = int(os.getenv("MCP_PORT", 5012))
LOCAL_CMDB_PATH = os.getenv("LOCAL_CMDB_PATH", "/data/cmdb.csv") # Example: CSV
SERVICENOW_INSTANCE = os.getenv("SERVICENOW_INSTANCE")
SERVICENOW_USER = os.getenv("SERVICENOW_USER")
SERVICENOW_PASSWORD_SECRET_PATH = os.getenv("SERVICENOW_PASSWORD_SECRET_PATH", "/run/secrets/servicenow_password")

# --- Backend Initialization --- 
mcp_server = FastMCP(name="cmdb-service", port=MCP_PORT)
local_cmdb_data = None
snow_client = None

def initialize_local_cmdb():
    global local_cmdb_data
    if not pd:
        logger.warning("Pandas library not installed. Local CSV CMDB backend disabled.")
        return
        
    if LOCAL_CMDB_PATH and os.path.exists(LOCAL_CMDB_PATH):
        try:
            # Example: Load CSV into a pandas DataFrame
            local_cmdb_data = pd.read_csv(LOCAL_CMDB_PATH)
            # Perform basic validation/cleaning if needed
            local_cmdb_data.columns = [col.lower().strip() for col in local_cmdb_data.columns]
            logger.info(f"Local CMDB data loaded successfully from: {LOCAL_CMDB_PATH}")
            logger.info(f"Local CMDB columns: {list(local_cmdb_data.columns)}")
        except Exception as e:
            logger.error(f"Failed to load or process local CMDB from {LOCAL_CMDB_PATH}: {e}", exc_info=True)
            local_cmdb_data = None
    else:
        logger.warning(f"Local CMDB path not configured or not found: {LOCAL_CMDB_PATH}")

def initialize_servicenow():
    global snow_client
    if SERVICENOW_INSTANCE and SERVICENOW_USER:
        # if not requests or not pysnow:
        #     logger.warning("Requests or pysnow library not installed. ServiceNow backend disabled.")
        #     return
        
        password = None
        try:
            if os.path.exists(SERVICENOW_PASSWORD_SECRET_PATH):
                with open(SERVICENOW_PASSWORD_SECRET_PATH, 'r') as f:
                    password = f.read().strip()
            else:
                logger.warning(f"ServiceNow password secret file not found at: {SERVICENOW_PASSWORD_SECRET_PATH}")
                # return # Cannot proceed without password

            if password:
                # Example using pysnow (uncomment imports and requirements)
                # snow_client = pysnow.Client(instance=SERVICENOW_INSTANCE, user=SERVICENOW_USER, password=password)
                # # Define default resources or test connection
                # snow_client.all(table='cmdb_ci_server', query=pysnow.QueryBuilder().AND().field('name').equals('test')).get(limit=1)
                logger.info(f"ServiceNow client initialized for instance: {SERVICENOW_INSTANCE} (Placeholder - requires library)")
            else:
                 logger.error("ServiceNow configured but password secret not found/readable.")

        except Exception as e:
            logger.error(f"Failed to initialize ServiceNow client: {e}", exc_info=True)
            snow_client = None
    else:
         logger.info("ServiceNow connection details not fully configured. ServiceNow backend disabled.")

initialize_local_cmdb()
initialize_servicenow()

# --- Health Check Endpoint ---
async def health_check(request): # Starlette request argument
    service_name = mcp_server.name if hasattr(mcp_server, 'name') else "cmdb-service" # Fallback for safety
    return JSONResponse({"status": "healthy", "service": service_name, "timestamp": time.time()})

# --- Tool Definitions ---

@mcp_server.tool("cmdb.local.getServerInfo")
def get_local_server_info(hostname: str) -> Optional[Dict[str, Any]]:
    """Retrieves server information from the local CMDB based on hostname."""
    logger.info(f"Querying local CMDB for server: {hostname}")
    if local_cmdb_data is None or hostname is None:
        logger.warning("Local CMDB not loaded or hostname not provided.")
        return None
    try:
        # Assuming a 'hostname' column exists
        result = local_cmdb_data[local_cmdb_data['hostname'].str.lower() == hostname.lower()]
        if not result.empty:
            # Convert the first match to a dictionary
            server_info = result.iloc[0].to_dict()
            logger.info(f"Found server '{hostname}' in local CMDB.")
            return server_info
        else:
            logger.info(f"Server '{hostname}' not found in local CMDB.")
            return None
    except KeyError:
         logger.error("Local CMDB does not contain a 'hostname' column.")
         return {"error": "Local CMDB missing 'hostname' column"}
    except Exception as e:
        logger.error(f"Error querying local CMDB for server '{hostname}': {e}", exc_info=True)
        return {"error": str(e)}

@mcp_server.tool("cmdb.local.findServers")
def find_local_servers(query_field: str, query_value: str) -> List[Dict[str, Any]]:
    """Finds servers in the local CMDB matching a specific field value (e.g., query_field='os', query_value='Ubuntu')."""
    logger.info(f"Searching local CMDB where {query_field} = {query_value}")
    if local_cmdb_data is None:
        logger.warning("Local CMDB not loaded.")
        return []
    try:
        field = query_field.lower().strip()
        if field not in local_cmdb_data.columns:
            logger.error(f"Query field '{field}' not found in local CMDB columns.")
            return []
            
        results = local_cmdb_data[local_cmdb_data[field].astype(str).str.contains(query_value, case=False, na=False)]
        
        if not results.empty:
            logger.info(f"Found {len(results)} servers matching {query_field}={query_value}.")
            return results.to_dict('records')
        else:
            logger.info(f"No servers found matching {query_field}={query_value}.")
            return []
    except Exception as e:
        logger.error(f"Error searching local CMDB: {e}", exc_info=True)
        return []

@mcp_server.tool("cmdb.servicenow.getCiDetails")
def get_servicenow_ci(sys_id: Optional[str] = None, name: Optional[str] = None, table: str = 'cmdb_ci') -> Optional[Dict[str, Any]]:
    """Retrieves Configuration Item (CI) details from ServiceNow by sys_id or name."""
    logger.info(f"Querying ServiceNow table '{table}' for CI: sys_id={sys_id}, name={name}")
    if not snow_client:
        logger.error("ServiceNow client not initialized.")
        return {"error": "ServiceNow client not available."}
    if not sys_id and not name:
         return {"error": "Either sys_id or name must be provided."}

    try:
        # Example using pysnow (uncomment imports and requirements)
        # resource = snow_client.resource(api_path=f'/table/{table}')
        # query = pysnow.QueryBuilder()
        # if sys_id:
        #     query.AND().field('sys_id').equals(sys_id)
        # if name:
        #      query.AND().field('name').equals(name)
        # response = resource.get(query=query, limit=1)
        # result = response.one_or_none()
        # if result:
        #     logger.info(f"Found CI in ServiceNow: {result.get('name', sys_id)}")
        #     return result
        # else:
        #      logger.info("CI not found in ServiceNow.")
        #      return None
        logger.warning("ServiceNow client library not fully implemented.") # Placeholder
        return {"status": "ServiceNow client library not fully implemented."} # Placeholder
    except Exception as e:
        logger.error(f"Error querying ServiceNow table '{table}': {e}", exc_info=True)
        return {"error": str(e)}

# --- Metrics Tool (Example) ---
@mcp_server.tool("cmdb.getMetrics")
def get_metrics() -> dict:
    """Returns basic operational metrics for the CMDB service."""
    # TODO: Implement actual metric tracking
    return {
        "status": "operational",
        "local_cmdb_loaded": local_cmdb_data is not None,
        "servicenow_client_initialized": snow_client is not None,
        "requests_processed": 0, # Replace with actual counter
        "errors_encountered": 0  # Replace with actual counter
    }

# --- Server Execution --- 
if __name__ == "__main__":
    logger.info(f"Starting CMDB MCP Server (12_cmdb_mcp) on port {MCP_PORT}")

    # Get the Starlette app from FastMCP
    app = mcp_server.sse_app()

    # Add the health check route
    health_route_exists = any(r.path == "/health" for r in getattr(app, 'routes', []))
    if not health_route_exists:
        if not hasattr(app, 'routes') or not isinstance(app.routes, list):
            logger.warning("Starlette app.routes is not a list, cannot append health route directly.")
            if hasattr(app, 'router') and hasattr(app.router, 'routes') and isinstance(app.router.routes, list):
                 app.router.routes.append(Route("/health", health_check))
                 logger.info("Health check route added to app.router.routes.")
            elif hasattr(app, 'routes') and isinstance(app.routes, list): 
                 app.routes.append(Route("/health", health_check))
                 logger.info("Health check route added to app.routes.")
            else:
                logger.error("Cannot add health check route: app.routes or app.router.routes list not found or not a list.")
        else: 
            app.routes.append(Route("/health", health_check))
            logger.info("Health check route added to app.routes.")
    else:
        logger.info("Health check route already exists.")

    try:
        host = getattr(mcp_server.settings, 'host', "0.0.0.0")
        log_level_setting = getattr(mcp_server.settings, 'log_level', "info")
        log_level = str(log_level_setting).lower() if log_level_setting is not None else "info"

        uvicorn.run(app, host=host, port=MCP_PORT, log_level=log_level)
        
    except Exception as e:
        logger.critical(f"CMDB MCP Server failed to run: {e}", exc_info=True)
        exit(1) 
import os
import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP

# Attempt to import backend libraries, log warnings if not installed
try:
    from pykeepass import PyKeePass
except ImportError:
    PyKeePass = None

try:
    from azure.keyvault.secrets import SecretClient
    from azure.identity import DefaultAzureCredential
    from azure.core.exceptions import ResourceNotFoundError as AzureResourceNotFoundError
except ImportError:
    SecretClient = None
    DefaultAzureCredential = None
    AzureResourceNotFoundError = None

try:
    from google.cloud import secretmanager
    from google.api_core import exceptions as GoogleApiExceptions
except ImportError:
    secretmanager = None
    GoogleApiExceptions = None

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("13_secrets_mcp")

# --- Configuration --- 
MCP_PORT = int(os.getenv("MCP_PORT", 8013))

# KeePass Config
KEEPASS_DB_PATH = os.getenv("KEEPASS_DB_PATH")
KEEPASS_PASSWORD_SECRET_PATH = os.getenv("KEEPASS_PASSWORD_SECRET_PATH", "/run/secrets/keepass_master_password")
KEEPASS_KEYFILE_PATH = os.getenv("KEEPASS_KEYFILE_PATH")

# Azure Key Vault Config
AZURE_VAULT_URL = os.getenv("AZURE_VAULT_URL")

# Google Secret Manager Config
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")

# --- Backend Client Initialization --- 
kp = None
azure_kv_client = None
gcp_sm_client = None

def initialize_backends():
    global kp, azure_kv_client, gcp_sm_client
    logger.info("Initializing secret backends...")

    # --- Initialize KeePass --- 
    if KEEPASS_DB_PATH and os.path.exists(KEEPASS_DB_PATH):
        if not PyKeePass:
            logger.warning("pykeepass library not installed. KeePass backend disabled.")
        else:
            keepass_password = None
            try:
                if os.path.exists(KEEPASS_PASSWORD_SECRET_PATH):
                    with open(KEEPASS_PASSWORD_SECRET_PATH, 'r') as f:
                        keepass_password = f.read().strip()
                    logger.info(f"Read KeePass password from secret file: {KEEPASS_PASSWORD_SECRET_PATH}")
                else:
                    logger.warning(f"KeePass password secret file not found at: {KEEPASS_PASSWORD_SECRET_PATH}")

                keyfile_exists = KEEPASS_KEYFILE_PATH and os.path.exists(KEEPASS_KEYFILE_PATH)
                if keyfile_exists:
                    logger.info(f"Using KeePass keyfile: {KEEPASS_KEYFILE_PATH}")

                if keepass_password or keyfile_exists:
                    try:
                        kp = PyKeePass(KEEPASS_DB_PATH, password=keepass_password, keyfile=KEEPASS_KEYFILE_PATH)
                        kp.reload()
                        logger.info(f"KeePass backend initialized successfully for DB: {KEEPASS_DB_PATH}")
                    except Exception as e:
                        logger.error(f"Failed to unlock or load KeePass DB: {e}", exc_info=False)
                        kp = None
                else:
                    logger.error("KeePass DB path specified but no password secret found/readable or keyfile provided/found.")
            except Exception as e:
                logger.error(f"Failed to initialize KeePass backend: {e}", exc_info=True)
    elif KEEPASS_DB_PATH:
         logger.warning(f"KEEPASS_DB_PATH specified but does not exist: {KEEPASS_DB_PATH}. KeePass backend disabled.")

    if AZURE_VAULT_URL:
        if not SecretClient or not DefaultAzureCredential:
            logger.warning("azure-keyvault-secrets or azure-identity not installed. AzureKV backend disabled.")
        else:
            try:
                credential = DefaultAzureCredential()
                azure_kv_client = SecretClient(vault_url=AZURE_VAULT_URL, credential=credential)
                logger.info(f"Azure Key Vault backend client initialized for URL: {AZURE_VAULT_URL}")
            except Exception as e:
                logger.error(f"Failed to initialize Azure Key Vault backend: {e}", exc_info=True)
                azure_kv_client = None

    if GCP_PROJECT_ID:
        if not secretmanager:
             logger.warning("google-cloud-secret-manager not installed. GCP SM backend disabled.")
        else:
            try:
                gcp_sm_client = secretmanager.SecretManagerServiceClient()
                logger.info(f"Google Secret Manager backend client initialized for project: {GCP_PROJECT_ID}")
            except Exception as e:
                logger.error(f"Failed to initialize Google Secret Manager backend: {e}", exc_info=True)
                gcp_sm_client = None

initialize_backends()

mcp_server = FastMCP(name="secrets-service", port=MCP_PORT)

@mcp_server.tool("secrets.getSecret")
def get_secret(secretName: str, version: Optional[str] = None) -> Optional[str]:
    logger.info(f"Received request for secret: '{secretName}' (version: {version or 'latest'}) via generic getSecret tool.")
    if secretName.startswith("keepass-"):
        entry_path = secretName.split('-', 1)[1].replace('-', '/')
        return get_keepass_entry(entry_path)
    elif secretName.startswith("azurekv-"):
         actual_secret_name = secretName.split('-', 1)[1]
         return get_azurekv_secret(actual_secret_name)
    elif secretName.startswith("gcpsm-"):
        actual_secret_name = secretName.split('-', 1)[1]
        return get_gcpsm_secret(actual_secret_name, version=version or 'latest')
    else:
        logger.warning(f"No backend convention matched for secret: '{secretName}'. Try specific tool if available.")
        return None

@mcp_server.tool("secrets.keepass.getEntry")
def get_keepass_entry(entryPath: str, field: str = 'password') -> Optional[str]:
    logger.info(f"Received request for KeePass entry: '{entryPath}', field: '{field}'")
    if not kp:
        logger.error("KeePass backend not initialized or failed to unlock.")
        return None
    try:
        kp.reload()
        entry = kp.find_entries(path=entryPath, first=True)
        if entry:
            value = None
            if field.lower() == 'password':
                value = entry.password
            elif field.lower() == 'username':
                value = entry.username
            elif field.lower() == 'notes':
                 value = entry.notes
            elif field.lower() == 'url':
                 value = entry.url
            elif entry.custom_properties and field in entry.custom_properties:
                value = entry.custom_properties[field]
            else:
                logger.warning(f"Field '{field}' not found for KeePass entry: '{entryPath}'")
                return None
            if value is not None:
                logger.info(f"Successfully retrieved field '{field}' for KeePass entry: '{entryPath}'")
                return value
            else:
                 logger.warning(f"Field '{field}' is empty for KeePass entry: '{entryPath}'")
                 return None
        else:
            logger.warning(f"KeePass entry not found at path: '{entryPath}'")
            return None
    except Exception as e:
        logger.error(f"Error retrieving KeePass entry '{entryPath}', field '{field}': {e}", exc_info=True)
        return None

@mcp_server.tool("secrets.azurekv.getSecret")
def get_azurekv_secret(secretName: str) -> Optional[str]:
    logger.info(f"Received request for Azure Key Vault secret: '{secretName}'")
    if not azure_kv_client:
         logger.error("Azure Key Vault backend not initialized.")
         return None
    try:
        retrieved_secret = azure_kv_client.get_secret(secretName)
        logger.info(f"Successfully retrieved Azure Key Vault secret: '{secretName}'")
        return retrieved_secret.value
    except AzureResourceNotFoundError:
        logger.warning(f"Azure Key Vault secret not found: '{secretName}'")
        return None
    except Exception as e:
        logger.error(f"Error retrieving Azure Key Vault secret '{secretName}': {e}", exc_info=True)
        return None

@mcp_server.tool("secrets.gcpsm.getSecret")
def get_gcpsm_secret(secretName: str, projectId: Optional[str] = None, version: str = 'latest') -> Optional[str]:
    logger.info(f"Received request for Google Secret Manager secret: '{secretName}' (Project: {projectId or GCP_PROJECT_ID or 'Default'}, Version: {version})")
    if not gcp_sm_client:
        logger.error("Google Secret Manager backend not initialized.")
        return None
    project = projectId or GCP_PROJECT_ID
    if not project:
         logger.error("GCP Project ID not configured for Google Secret Manager.")
         return None
    name = gcp_sm_client.secret_version_path(project, secretName, version)
    try:
        response = gcp_sm_client.access_secret_version(request={"name": name})
        payload = response.payload.data.decode("UTF-8")
        logger.info(f"Successfully retrieved Google Secret Manager secret: '{secretName}' version '{version}'")
        return payload
    except GoogleApiExceptions.NotFound:
        logger.warning(f"Google Secret Manager secret not found: '{name}'")
        return None
    except Exception as e:
        logger.error(f"Error retrieving Google Secret Manager secret '{name}': {e}", exc_info=True)
        return None

@mcp_server.tool("secrets.getMetrics")
def get_metrics() -> dict:
    return {
        "status": "operational",
        "initialized_backends": {
            "keepass": kp is not None,
            "azure_kv": azure_kv_client is not None,
            "gcp_sm": gcp_sm_client is not None
        },
        "requests_processed": 0, 
        "errors_encountered": 0
    }

# --- Server Execution --- 
if __name__ == "__main__":
    logger.info(f"Starting Secrets MCP Server (13_secrets_mcp) on port {MCP_PORT} using mcp_server.run()")
    try:
        mcp_server.run() # Call run() without reload, assuming it should block
    except Exception as e:
        logger.critical(f"Secrets MCP Server failed to run: {e}", exc_info=True)
        exit(1)
    logger.info("mcp_server.run() has exited.") # This should ideally not be reached if run() is blocking

    if server_started_successfully:
        logger.info("mcp_server.run() called. Assuming server is running in background or has exited.")
        # If mcp_server.run() is non-blocking and starts a background process,
        # keep the main script alive. Otherwise, this does nothing if run() was blocking.
        try:
            while True:
                import time
                time.sleep(60) # Keep main thread alive
                logger.info("Main thread still alive in mcp_server.py...") # Log to show it's working
        except KeyboardInterrupt:
            logger.info("mcp_server.py: Main thread received KeyboardInterrupt. Exiting.")
        finally:
            logger.info("mcp_server.py: Main thread exiting.")
    else:
        logger.error("mcp_server.run() did not seem to start the server successfully or it exited immediately.") 
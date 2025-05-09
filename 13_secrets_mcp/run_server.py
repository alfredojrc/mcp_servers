import logging
import sys
import os

# THIS IS RUN_SERVER.PY
print("DEBUG: TOP OF RUN_SERVER.PY EXECUTING", flush=True)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("run_server")

logger.info(f"DEBUG: run_server.py - PYTHONPATH: {os.getenv('PYTHONPATH')}")
logger.info(f"DEBUG: run_server.py - sys.path: {sys.path}")

try:
    # Import the mcp_server instance from your main server file
    from mcp_server import mcp_server, MCP_PORT # also import MCP_PORT for logging
    logger.info("DEBUG: run_server.py - Successfully imported mcp_server and MCP_PORT")
except ImportError as e:
    logger.error(f"DEBUG: run_server.py - FAILED TO IMPORT mcp_server: {e}", exc_info=True)
    exit(1)
except Exception as e:
    logger.error(f"DEBUG: run_server.py - UNEXPECTED ERROR DURING IMPORT: {e}", exc_info=True)
    exit(1)

if __name__ == "__main__":
    logger.info(f"Wrapper script 'run_server.py' __main__ starting FastMCP server on port {MCP_PORT} with reload=True.")
    try:
        # Call the run method of the imported FastMCP instance
        # The reload=True seemed to keep the container from exiting immediately in one of our tests.
        mcp_server.run(reload=True)
    except TypeError:
        logger.warning("run_server.py: mcp_server.run() does not accept 'reload' parameter. Running without it.")
        mcp_server.run()
    except Exception as e:
        logger.critical(f"run_server.py: Secrets MCP Server failed to run: {e}", exc_info=True)
        exit(1)
    logger.info("run_server.py: mcp_server.run() has exited.") # Should not be reached if server runs indefinitely 
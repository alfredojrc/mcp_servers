import os
import logging
import subprocess
import shlex
import datetime
import time
from typing import Optional
# import paramiko # Uncomment if using SSH
from threading import Thread

from mcp.server.fastmcp import FastMCP
from prometheus_client import start_http_server, Counter, Gauge, Histogram, Summary

# Setup basic logging according to project standard (ideally JSON)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("01_linux_cli_mcp")

# Configuration from environment variables
MCP_PORT = int(os.getenv("MCP_PORT", 5001))
METRICS_PORT = int(os.getenv("METRICS_PORT", 9091))
ALLOWED_COMMANDS = os.getenv("ALLOWED_COMMANDS", "ls,cat,grep,ps,df,echo").split(',')
ALLOWED_READ_PATHS = os.getenv("ALLOWED_READ_PATHS", "/tmp:/var/log").split(':')
ALLOWED_WRITE_PATHS = os.getenv("ALLOWED_WRITE_PATHS", "/tmp").split(':')
# SSH_HOSTS = os.getenv("SSH_HOSTS", "").split(',') # Uncomment if using SSH
# SSH_USER = os.getenv("SSH_USER") # Uncomment if using SSH
# SSH_KEY_SECRET_PATH = os.getenv("SSH_KEY_SECRET_PATH") # Uncomment if using SSH

# --- Metrics Definitions ---
# Use Summary for latency as it includes quantiles, Histogram is another option
TOOL_LATENCY = Summary('mcp_tool_latency_seconds', 'Latency of MCP tool execution', ['tool_name'])
TOOL_CALLS_TOTAL = Counter('mcp_tool_calls_total', 'Total calls to MCP tools', ['tool_name'])
TOOL_ERRORS_TOTAL = Counter('mcp_tool_errors_total', 'Total errors encountered during MCP tool execution', ['tool_name'])
# Example Gauge (can increase/decrease)
# ACTIVE_CONNECTIONS = Gauge('mcp_active_connections', 'Number of active MCP connections')

# Initialize FastMCP server
mcp_server = FastMCP(name="linux-cli-service", port=MCP_PORT)

# --- Helper Functions (Security Critical!) ---
def is_path_allowed(path, allowed_paths):
    """Checks if a given path is within one of the allowed base paths."""
    # Basic check, consider more robust path normalization and validation
    try:
        absolute_path = os.path.abspath(path)
        for allowed in allowed_paths:
            if os.path.commonpath([absolute_path, os.path.abspath(allowed)]) == os.path.abspath(allowed):
                return True
    except ValueError:
        # Handle potential issues with path manipulation
        pass
    logger.warning(f"Path access denied: {path}. Not within allowed paths: {allowed_paths}")
    return False

def is_command_allowed(command_str):
    """Checks if the base command is in the allowed list."""
    try:
        # Basic check, consider more robust command parsing
        base_command = shlex.split(command_str)[0]
        if base_command in ALLOWED_COMMANDS:
            return True
    except IndexError:
         pass # Handle empty command string
    except Exception as e:
        logger.error(f"Error parsing command for allowlist check: {command_str} - {e}")

    logger.warning(f"Command execution denied: {command_str}. Base command not in allowed list: {ALLOWED_COMMANDS}")
    return False

def run_local_command(command, cwd=None, timeout=60):
    """Securely runs a local command using subprocess."""
    if not is_command_allowed(command):
        return {"error": "Command not allowed"}

    # CRITICAL: Input sanitization should happen *before* this point if command includes user input
    # For simplicity, we assume the 'command' string is pre-validated/constructed safely
    logger.info(f"Executing command: {command}")
    try:
        # Use shell=False if possible by splitting command, but shell=True is needed for pipes, etc.
        # If shell=True, the command MUST be trusted/validated.
        process = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout, cwd=cwd, check=False) # check=False to handle non-zero exits
        return {
            "stdout": process.stdout,
            "stderr": process.stderr,
            "exit_code": process.returncode
        }
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {command}")
        return {"error": "Command timed out"}
    except Exception as e:
        logger.error(f"Error executing command: {command} - {e}", exc_info=True)
        return {"error": f"Failed to execute command: {e}"}

def create_backup(path):
    """Creates a backup of a file."""
    if not os.path.exists(path):
        return False # Cannot backup non-existent file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{path}.BAK_{timestamp}"
    try:
        # Using subprocess for 'cp' might be safer depending on permissions
        subprocess.run(['cp', path, backup_path], check=True)
        logger.info(f"Created backup: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup for {path}: {e}", exc_info=True)
        return False

# --- Tool Definitions (Instrumented) ---
@mcp_server.tool("os.linux.cli.getOsInfo")
@TOOL_LATENCY.labels(tool_name='os.linux.cli.getOsInfo').time()
def get_os_info() -> dict:
    """Gets OS release information from /etc/os-release."""
    TOOL_CALLS_TOTAL.labels(tool_name='os.linux.cli.getOsInfo').inc()
    try:
        # Prefer reading /etc/os-release as it's standard
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release", 'r') as f:
                lines = f.readlines()
                return dict(line.strip().split('=', 1) for line in lines if '=' in line)
        else:
            # Fallback or alternative method if needed
             result = run_local_command("lsb_release -a")
             if result.get("exit_code") == 0:
                 return {"output": result["stdout"]}
             else:
                return {"error": "Could not determine OS info", "details": result.get("stderr")}
    except Exception as e:
        TOOL_ERRORS_TOTAL.labels(tool_name='os.linux.cli.getOsInfo').inc()
        logger.error(f"Error getting OS info: {e}", exc_info=True)
        return {"error": str(e)}

@mcp_server.tool("os.linux.cli.runCommand")
@TOOL_LATENCY.labels(tool_name='os.linux.cli.runCommand').time()
def run_command_tool(command: str, cwd: Optional[str] = None, timeout: int = 60, requires_approval: bool = True) -> dict:
    """Executes a shell command using /bin/bash -c. Requires approval by default unless command is known read-only and allowed."""
    TOOL_CALLS_TOTAL.labels(tool_name='os.linux.cli.runCommand').inc()
    # TODO: Implement approval check mechanism (needs context from host/LLM)
    is_read_only_command = False # Basic check - enhance this logic
    if command.split(' ')[0] in ['ls', 'cat', 'grep', 'ps', 'df', 'echo', 'ceph', 'nginx', 'systemctl', 'getent'] and 'status' in command or '-t' in command:
        is_read_only_command = True

    if requires_approval and not is_read_only_command:
        # In a real system, this would likely involve a callback or state check
        # provided by the orchestrator (00_master_mcp) or user.
        logger.warning(f"Approval required but mechanism not implemented for command: {command}")
        TOOL_ERRORS_TOTAL.labels(tool_name='os.linux.cli.runCommand').inc()
        return {"error": "Approval required for this command"}

    # SECURITY: Ensure command doesn't contain obviously dangerous patterns
    # This is basic; production needs robust input validation/sanitization
    if ';' in command or '&&' in command or '||' in command or 'rm -rf' in command:
         logger.error(f"Potentially dangerous command pattern rejected: {command}")
         TOOL_ERRORS_TOTAL.labels(tool_name='os.linux.cli.runCommand').inc()
         return {"error": "Command rejected due to potentially dangerous pattern."}

    # Use the secure helper function
    result = run_local_command(command, cwd=cwd, timeout=timeout)
    if result.get("error"):
        TOOL_ERRORS_TOTAL.labels(tool_name='os.linux.cli.runCommand').inc()
    return result

@mcp_server.tool("os.linux.cli.readFile")
@TOOL_LATENCY.labels(tool_name='os.linux.cli.readFile').time()
def read_file_tool(path: str) -> str:
    """Reads the content of an allowed file."""
    TOOL_CALLS_TOTAL.labels(tool_name='os.linux.cli.readFile').inc()
    if not is_path_allowed(path, ALLOWED_READ_PATHS):
        TOOL_ERRORS_TOTAL.labels(tool_name='os.linux.cli.readFile').inc()
        return f"Error: Access denied to read path {path}"
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        TOOL_ERRORS_TOTAL.labels(tool_name='os.linux.cli.readFile').inc()
        logger.error(f"Error reading file {path}: {e}", exc_info=True)
        return f"Error reading file: {e}"

@mcp_server.tool("os.linux.cli.writeFile")
@TOOL_LATENCY.labels(tool_name='os.linux.cli.writeFile').time()
def write_file_tool(path: str, content: str, append: bool = False, requires_approval: bool = True) -> str:
    """Writes content to an allowed file. Creates backups. Requires approval."""
    TOOL_CALLS_TOTAL.labels(tool_name='os.linux.cli.writeFile').inc()
    # TODO: Implement approval check mechanism
    if requires_approval:
        logger.warning(f"Approval required but mechanism not implemented for writeFile: {path}")
        TOOL_ERRORS_TOTAL.labels(tool_name='os.linux.cli.writeFile').inc()
        return "Error: Approval required to write file"

    if not is_path_allowed(path, ALLOWED_WRITE_PATHS):
        TOOL_ERRORS_TOTAL.labels(tool_name='os.linux.cli.writeFile').inc()
        return f"Error: Access denied to write path {path}"

    # Backup before writing
    if not append and os.path.exists(path):
        if not create_backup(path):
            TOOL_ERRORS_TOTAL.labels(tool_name='os.linux.cli.writeFile').inc()
            return f"Error: Failed to create backup for {path}"

    mode = 'a' if append else 'w'
    try:
        with open(path, mode) as f:
            f.write(content)
        logger.info(f"Successfully wrote to file: {path}")
        return f"Successfully wrote to {path}"
    except Exception as e:
        TOOL_ERRORS_TOTAL.labels(tool_name='os.linux.cli.writeFile').inc()
        logger.error(f"Error writing file {path}: {e}", exc_info=True)
        return f"Error writing file: {e}"

# --- Add other namespaced tools here (nginx, ceph, etc.) following the pattern ---
# Example:
# @mcp_server.tool("os.linux.nginx.reloadConfig")
# @TOOL_LATENCY.labels(tool_name='os.linux.nginx.reloadConfig').time()
# def nginx_reload(requires_approval: bool = True) -> dict:
#     TOOL_CALLS_TOTAL.labels(tool_name='os.linux.nginx.reloadConfig').inc()
#     if requires_approval:
#         TOOL_ERRORS_TOTAL.labels(tool_name='os.linux.nginx.reloadConfig').inc()
#         return {"error": "Approval required"}
#     result = run_local_command("nginx -s reload")
#     if result.get("error"):
#          TOOL_ERRORS_TOTAL.labels(tool_name='os.linux.nginx.reloadConfig').inc()
#     return result

# --- Metrics Server Thread ---
def start_metrics_server(port):
    try:
        start_http_server(port)
        logger.info(f"Prometheus metrics server started on port {port}")
    except Exception as e:
        logger.error(f"Failed to start Prometheus metrics server: {e}", exc_info=True)

# --- Main Execution ---
if __name__ == "__main__":
    # Start metrics server in a background thread
    metrics_thread = Thread(target=start_metrics_server, args=(METRICS_PORT,), daemon=True)
    metrics_thread.start()

    logger.info(f"Starting Linux CLI MCP Server on port {MCP_PORT}")
    try:
        # The run() method likely starts the underlying web server (e.g., Uvicorn/Hypercorn)
        mcp_server.run()
    except Exception as e:
        logger.critical(f"Linux CLI MCP Server failed to run: {e}", exc_info=True)
        exit(1) 
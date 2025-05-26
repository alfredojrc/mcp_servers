import os
import logging
import subprocess
import shlex
import datetime
import time
from typing import Optional
# import paramiko # Uncomment if using SSH
from threading import Thread

# Add these imports for JSON logging
import json
from datetime import datetime as dt # Alias to avoid conflict with datetime module

from mcp.server.fastmcp import FastMCP
from prometheus_client import start_http_server, Counter, Gauge, Histogram, Summary

# Add these imports
from starlette.routing import Route
from starlette.responses import JSONResponse
import uvicorn

# --- JSON Formatter Class ---
class JSONFormatter(logging.Formatter):
    def __init__(self, service_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service_name = service_name

    def format(self, record):
        log_entry = {
            "timestamp": dt.now().isoformat(), # Use aliased dt
            "service": self.service_name,
            "level": record.levelname,
            "message": record.getMessage(),
            "correlation_id": getattr(record, 'correlation_id', None)
        }
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        if record.stack_info:
            log_entry['stack_info'] = self.formatStack(record.stack_info)
        return json.dumps(log_entry)

# --- Logging Setup ---
# Get the root logger
root_logger = logging.getLogger()
# Remove any existing handlers
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Create and add the new JSON formatter
# The service name for this specific service
SERVICE_NAME_FOR_LOGGING = "linux-cli-service" 
json_formatter = JSONFormatter(SERVICE_NAME_FOR_LOGGING)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(json_formatter)
root_logger.addHandler(stream_handler)
root_logger.setLevel(logging.INFO) # Set level on the root logger

# Get the specific logger for this module, it will inherit the root logger's config
logger = logging.getLogger(__name__) # Use __name__ for module-specific logger is a common practice

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

# --- Security Validator Class ---
class SecurityValidator:
    def __init__(self, allowed_commands, allowed_read_paths, allowed_write_paths, logger_instance):
        self.allowed_commands = allowed_commands
        self.allowed_read_paths = allowed_read_paths
        self.allowed_write_paths = allowed_write_paths
        self.logger = logger_instance

    def is_path_allowed(self, path, path_type="read"):
        allowed_paths_list = self.allowed_read_paths if path_type == "read" else self.allowed_write_paths
        try:
            # Defensive coding: ensure path is a string
            if not isinstance(path, str):
                self.logger.warning(f"Path validation failed: path is not a string ({type(path)}). Denying access.")
                return False
            absolute_path = os.path.abspath(path)
            for allowed_base_path in allowed_paths_list:
                # Ensure allowed_base_path is also a string and valid path component
                if not isinstance(allowed_base_path, str) or not allowed_base_path:
                    self.logger.error(f"Invalid allowed path configuration: '{allowed_base_path}'. Skipping.")
                    continue
                abs_allowed_base_path = os.path.abspath(allowed_base_path)
                if os.path.commonpath([absolute_path, abs_allowed_base_path]) == abs_allowed_base_path:
                    return True
        except ValueError as e:
            self.logger.error(f"Path validation error for path '{path}': {e}")
            pass # Path manipulation error, deny access
        self.logger.warning(f"Path access denied: {path} (type: {path_type}). Not within allowed paths: {allowed_paths_list}")
        return False

    def is_command_in_allowlist(self, command_str):
        try:
            # Ensure command_str is a string
            if not isinstance(command_str, str) or not command_str.strip():
                self.logger.warning(f"Command allowlist check failed: command is empty or not a string.")
                return False
            base_command = shlex.split(command_str)[0]
            if base_command in self.allowed_commands:
                return True
        except IndexError:
            self.logger.warning(f"Command allowlist check failed for '{command_str}': No command found after parsing.")
            return False # Handle empty command string or parsing issue
        except Exception as e:
            self.logger.error(f"Error parsing command for allowlist check: {command_str} - {e}")
            return False # Deny on error
        
        # Log denied command only if it was parsed successfully but not in allowlist
        parsed_base_command = "<parsing_failed>"
        try: parsed_base_command = shlex.split(command_str)[0]
        except: pass
        self.logger.warning(f"Command execution denied: Base command '{parsed_base_command}' from '{command_str}' not in allowed list: {self.allowed_commands}")
        return False

    def validate_command_patterns(self, command_str):
        if not isinstance(command_str, str):
             self.logger.warning("Command pattern validation failed: command is not a string.")
             return False, "Command not a string"

        dangerous_patterns = [';', '&&', '||', '`', '$('] 
        explicitly_dangerous_substrings = ['rm -rf', '> /dev/sd', 'mkfs'] 

        for pattern in dangerous_patterns:
            if pattern in command_str:
                self.logger.error(f"Potentially dangerous pattern '{pattern}' rejected in command: {command_str}")
                return False, f"Dangerous pattern '{pattern}'"
        
        for substring in explicitly_dangerous_substrings:
            if substring in command_str: 
                self.logger.error(f"Potentially dangerous substring '{substring}' rejected in command: {command_str}")
                return False, f"Dangerous substring '{substring}'"
        return True, "Pattern check passed"

    def validate_command_for_execution(self, command_str):
        if not self.is_command_in_allowlist(command_str):
            return False, "Command not in allowlist."
        
        pattern_safe, pattern_reason = self.validate_command_patterns(command_str)
        if not pattern_safe:
            return False, pattern_reason
            
        return True, "Command validated for execution."

# Instantiate the SecurityValidator
# logger should be defined from the logging setup above
security_validator = SecurityValidator(ALLOWED_COMMANDS, ALLOWED_READ_PATHS, ALLOWED_WRITE_PATHS, logger)

# --- Health Check Endpoint ---
async def health_check(request): # Starlette request argument
    service_name = mcp_server.name if hasattr(mcp_server, 'name') else "linux-cli-service" # Fallback for safety
    return JSONResponse({"status": "healthy", "service": service_name, "timestamp": time.time()})

# --- Helper Functions (Security Critical!) ---
# Removed old is_path_allowed and is_command_allowed as they are now methods in SecurityValidator

def run_local_command(command, cwd=None, timeout=60):
    """Securely runs a local command using subprocess."""
    # Use the SecurityValidator instance
    is_safe, reason = security_validator.validate_command_for_execution(command)
    if not is_safe:
        # Log the specific reason for failure before returning
        logger.error(f"Command validation failed for '{command}': {reason}")
        return {"error": f"Command validation failed: {reason}"}

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

    # Approval check (remains the same)
    is_read_only_command = False 
    # Basic read-only check, can be enhanced within SecurityValidator if needed or kept here for tool-specific logic
    # For now, keep this simple read-only check here as it's tied to the requires_approval logic.
    # A more sophisticated system might involve SecurityValidator classifying commands.
    try:
        # Check if command is not empty and is a string before trying to split
        if command and isinstance(command, str) and command.strip():
            first_word = command.strip().split(' ')[0]
            if first_word in ['ls', 'cat', 'grep', 'ps', 'df', 'echo', 'ceph', 'nginx', 'systemctl', 'getent'] and \
               ('status' in command or '-t' in command or first_word in ['ls', 'cat', 'grep', 'ps', 'df', 'echo']): # Simplified this for clarity
                is_read_only_command = True
    except Exception as e:
        logger.warning(f"Could not parse command '{command}' for read-only check: {e}")

    if requires_approval and not is_read_only_command:
        logger.warning(f"Approval required but mechanism not implemented for command: {command}")
        TOOL_ERRORS_TOTAL.labels(tool_name='os.linux.cli.runCommand').inc()
        return {"error": "Approval required for this command"}

    # Security validation is now primarily handled by run_local_command via SecurityValidator
    # The dangerous pattern check `if ';' in command...` is removed from here.

    result = run_local_command(command, cwd=cwd, timeout=timeout)
    if result.get("error"):
        # Avoid double-incrementing if error was from validation inside run_local_command
        # However, run_local_command doesn't increment TOOL_ERRORS_TOTAL itself.
        # So, if run_local_command returns an error (either validation or execution), it should be counted here.
        TOOL_ERRORS_TOTAL.labels(tool_name='os.linux.cli.runCommand').inc()
    return result

@mcp_server.tool("os.linux.cli.readFile")
@TOOL_LATENCY.labels(tool_name='os.linux.cli.readFile').time()
def read_file_tool(path: str) -> str:
    """Reads the content of an allowed file."""
    TOOL_CALLS_TOTAL.labels(tool_name='os.linux.cli.readFile').inc()
    # Use the SecurityValidator instance
    if not security_validator.is_path_allowed(path, "read"):
        TOOL_ERRORS_TOTAL.labels(tool_name='os.linux.cli.readFile').inc()
        # The validator already logs, so we just return the error message.
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

    # Use the SecurityValidator instance
    if not security_validator.is_path_allowed(path, "write"):
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
    
    # Get the Starlette app from FastMCP
    app = mcp_server.sse_app()

    # Add the health check route
    # Ensure the route is not added multiple times if uvicorn reloads the code
    health_route_exists = any(r.path == "/health" for r in getattr(app, 'routes', []))
    if not health_route_exists:
        # Make sure app.routes is a list that can be appended to
        if not hasattr(app, 'routes') or not isinstance(app.routes, list):
            logger.warning("Starlette app.routes is not a list, cannot append health route directly. This might indicate an issue or a different Starlette version structure.")
            # As a fallback, one might need to create a new Starlette app and mount mcp_app,
            # but for now, we assume app.routes is a list.
            # If it's a Router instance, it might have an 'add_route' method.
            # For simplicity with FastMCP's sse_app structure, direct append is tried.
            # If app.router exists and has an 'routes' attribute (newer Starlette)
            if hasattr(app, 'router') and hasattr(app.router, 'routes') and isinstance(app.router.routes, list):
                 app.router.routes.append(Route("/health", health_check))
                 logger.info("Health check route added to app.router.routes.")
            elif hasattr(app, 'routes') and isinstance(app.routes, list): # older Starlette or direct list
                 app.routes.append(Route("/health", health_check))
                 logger.info("Health check route added to app.routes.")
            else:
                logger.error("Cannot add health check route: app.routes or app.router.routes list not found or not a list.")

        else: # app.routes is a list
            app.routes.append(Route("/health", health_check))
            logger.info("Health check route added to app.routes.")
    else:
        logger.info("Health check route already exists.")

    try:
        # Replicate the relevant part of FastMCP's run_sse_async
        host = getattr(mcp_server.settings, 'host', "0.0.0.0")
        log_level_setting = getattr(mcp_server.settings, 'log_level', "info")
        
        # Ensure log_level is a string (uvicorn expects string or None)
        log_level = str(log_level_setting).lower() if log_level_setting is not None else "info"

        # Instead of mcp_server.run(), we use uvicorn.run with the modified app
        uvicorn.run(app, host=host, port=MCP_PORT, log_level=log_level)

    except Exception as e:
        logger.critical(f"Linux CLI MCP Server failed to run: {e}", exc_info=True)
        exit(1) 
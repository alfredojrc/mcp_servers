import os
import logging
import subprocess
import shlex
import datetime
import time
from typing import Optional, List, Dict, Any, Tuple
import asyncio
import uuid
# import paramiko # Uncomment if using SSH
from threading import Thread

# Add these imports for JSON logging
import json
from datetime import datetime as dt # Alias to avoid conflict with datetime module

from mcp.server.fastmcp import FastMCP
from prometheus_client import start_http_server, Counter, Gauge, Histogram, Summary

# Add these imports
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
from starlette.applications import Starlette
import uvicorn
from mcp.server.sse import SseServerTransport

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
MCP_PORT = int(os.getenv("MCP_PORT", "8001"))
# METRICS_PORT = int(os.getenv("METRICS_PORT", 9091)) # Removed
ALLOWED_COMMANDS_STR = os.getenv("ALLOWED_COMMANDS", "ls,cat,grep,ps,df,echo,stat,head,tail,find,ssh,uptime")
ALLOWED_COMMANDS = [cmd.strip() for cmd in ALLOWED_COMMANDS_STR.split(',')]
ALLOWED_READ_PATHS_STR = os.getenv("ALLOWED_READ_PATHS", "/etc:/var/log:/tmp:/home")
ALLOWED_READ_PATHS = [path.strip() for path in ALLOWED_READ_PATHS_STR.split(':')]
ALLOWED_WRITE_PATHS_STR = os.getenv("ALLOWED_WRITE_PATHS", "/tmp")
ALLOWED_WRITE_PATHS = [path.strip() for path in ALLOWED_WRITE_PATHS_STR.split(':')]

# SSH Configuration
SSH_HOSTS_STR = os.getenv("SSH_HOSTS")
SSH_CONFIG: Dict[str, Dict[str, str]] = {}
if SSH_HOSTS_STR:
    # Assuming SSH_USER and SSH_KEY_SECRET_PATH are global for all SSH_HOSTS for simplicity
    # If per-host config is needed, SSH_HOSTS could be a JSON string or structured differently
    ssh_user = os.getenv("SSH_USER")
    ssh_key_path = os.getenv("SSH_KEY_SECRET_PATH")
    if ssh_user and ssh_key_path:
        for host in SSH_HOSTS_STR.split(','):
            host = host.strip()
            if host:
                SSH_CONFIG[host] = {"user": ssh_user, "key_path": ssh_key_path}
        logger.info(f"SSH configured for hosts: {list(SSH_CONFIG.keys())}")
    else:
        logger.warning("SSH_HOSTS is set, but SSH_USER or SSH_KEY_SECRET_PATH is missing. SSH functionality will be limited.")

# --- Metrics Definitions ---
# Use Summary for latency as it includes quantiles, Histogram is another option
TOOL_LATENCY = Summary('mcp_tool_latency_seconds', 'Latency of MCP tool execution', ['tool_name'])
TOOL_CALLS_TOTAL = Counter('mcp_tool_calls_total', 'Total calls to MCP tools', ['tool_name'])
TOOL_ERRORS_TOTAL = Counter('mcp_tool_errors_total', 'Total errors encountered during MCP tool execution', ['tool_name'])
# Example Gauge (can increase/decrease)
# ACTIVE_CONNECTIONS = Gauge('mcp_active_connections', 'Number of active MCP connections')

# Initialize FastMCP server
mcp_server = FastMCP(name="linux-cli-service", port=MCP_PORT, host="0.0.0.0")

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

# --- Helper function to create the SSE application ---
def create_sse_application(mcp_instance: FastMCP) -> Starlette:
    """Create a Starlette app that handles SSE connections and message handling"""
    # The transport handles the SSE protocol details.
    # Tool call messages will be expected at the '/messages/' path relative to where this app is mounted.
    transport = SseServerTransport("/messages") # Note: removed trailing slash, FastMCP examples vary

    # Define handler functions
    async def handle_sse_connection(request): # Renamed for clarity
        """Handles the GET /sse endpoint for establishing the SSE connection."""
        # This uses the SseServerTransport to manage the connection lifecycle.
        # The mcp_instance._mcp_server.run is the core MCP processing loop.
        # It needs the input and output streams provided by transport.connect_sse.
        async with transport.connect_sse(
            request.scope, request.receive, request._send # request._send is an internal Starlette mechanism
        ) as streams:
            # The streams are (read_stream, write_stream)
            # Pass these to the underlying McpServer's run method.
            await mcp_instance._mcp_server.run(
                streams[0], streams[1], mcp_instance._mcp_server.create_initialization_options()
            )

    # Create Starlette routes
    # GET /sse for establishing the connection
    # POST /messages for sending tool calls (handled by transport.handle_post_message)
    routes = [
        Route("/sse", endpoint=handle_sse_connection, methods=["GET"]),
        Mount("/messages", app=transport.handle_post_message), # Handles POST for tool calls
        Route("/health", endpoint=health_check, methods=["GET"]), # Standard health check
        Route("/direct_tool_call", endpoint=handle_direct_tool_call, methods=["POST"]) # New direct tool call endpoint
    ]

    # Create and return the Starlette app
    sse_app = Starlette(routes=routes)
    logger.info(f"Created Starlette SSE application with routes: /sse (GET), /messages (POST), /health (GET), /direct_tool_call (POST)")
    return sse_app

# --- New Direct Tool Call Handler ---
async def handle_direct_tool_call(request): # Starlette request argument
    try:
        json_rpc_request = await request.json()
        if not isinstance(json_rpc_request, dict) or \
           json_rpc_request.get("jsonrpc") != "2.0" or \
           "method" not in json_rpc_request or \
           "params" not in json_rpc_request or \
           "id" not in json_rpc_request:
            return JSONResponse({"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": None}, status_code=400)

        json_rpc_id = json_rpc_request.get("id")
        mcp_pdu = json_rpc_request.get("params")

        if not isinstance(mcp_pdu, dict) or \
           mcp_pdu.get("type") != "tool_call" or \
           "tool_name" not in mcp_pdu or \
           "parameters" not in mcp_pdu:
            # This is an MCP PDU validation error, but we need to return a JSON-RPC error
            return JSONResponse({"jsonrpc": "2.0", "error": {"code": -32602, "message": "Invalid params: Malformed MCP PDU"}, "id": json_rpc_id}, status_code=400)

        tool_name = mcp_pdu["tool_name"]
        tool_params = mcp_pdu.get("parameters", {})

        # Access the tool through FastMCP's tool manager
        tool_obj = None
        tool_function = None
        
        # Try multiple approaches to find the tool
        # 1. Try via _tool_manager
        if hasattr(mcp_server, '_tool_manager') and hasattr(mcp_server._tool_manager, '_tools'):
            logger.info(f"DIAGNOSTIC: Keys in _tool_manager._tools: {list(mcp_server._tool_manager._tools.keys())}")
            tool_obj = mcp_server._tool_manager._tools.get(tool_name)
            if tool_obj:
                tool_function = tool_obj.fn if hasattr(tool_obj, 'fn') else tool_obj
        
        # 2. Try via _mcp_server.tools (fallback)
        if not tool_function and hasattr(mcp_server, '_mcp_server') and hasattr(mcp_server._mcp_server, 'tools'):
            logger.info(f"DIAGNOSTIC: Keys in _mcp_server.tools: {list(mcp_server._mcp_server.tools.keys())}")
            tool_obj = mcp_server._mcp_server.tools.get(tool_name)
            if tool_obj:
                tool_function = tool_obj.fn if hasattr(tool_obj, 'fn') else tool_obj
        
        # 3. Try to call the tool directly via FastMCP's call_tool method
        if not tool_function and hasattr(mcp_server, 'call_tool'):
            try:
                logger.info(f"Attempting to use FastMCP's call_tool method for '{tool_name}'")
                # FastMCP's call_tool is async
                result = await mcp_server.call_tool(tool_name, tool_params)
                response_mcp_pdu = {
                    "mcp_version": "2.0",
                    "id": mcp_pdu.get("id", str(uuid.uuid4())),
                    "type": "tool_result",
                    "tool_name": tool_name,
                    "result": result,
                    "context": mcp_pdu.get("context", {})
                }
                return JSONResponse({"jsonrpc": "2.0", "result": response_mcp_pdu, "id": json_rpc_id})
            except Exception as e:
                logger.error(f"FastMCP call_tool failed for '{tool_name}': {e}")
                # Continue to the error response below
        
        if not tool_function:
            logger.error(f"Tool '{tool_name}' not found in any tool registry.")
            return JSONResponse({"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method not found: Tool '{tool_name}' not found"}, "id": json_rpc_id}, status_code=404)

        # Execute the tool function
        # Need to handle both sync and async tool functions
        # FastMCP handles this internally when calling through its main loop.
        # Here, we might need a more direct approach or rely on tool functions being async.
        # For now, let's assume they are awaitable or FastMCP wraps them to be.
        try:
            # Pass parameters as keyword arguments
            if asyncio.iscoroutinefunction(tool_function):
                result = await tool_function(**tool_params)
            else:
                result = tool_function(**tool_params)
            
            response_mcp_pdu = {
                "mcp_version": "2.0",
                "id": mcp_pdu.get("id", str(uuid.uuid4())), # Reuse PDU ID if available
                "type": "tool_result",
                "tool_name": tool_name,
                "result": result,
                "context": mcp_pdu.get("context", {})
            }
            return JSONResponse({"jsonrpc": "2.0", "result": response_mcp_pdu, "id": json_rpc_id})

        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}' directly: {e}", exc_info=True)
            # Construct an MCP tool_error PDU
            error_pdu_content = {
                "type": "error", # MCP error type
                "message": str(e),
                # Add more details if possible, e.g., traceback for debugging if appropriate
            }
            response_mcp_pdu = {
                "mcp_version": "2.0",
                "id": mcp_pdu.get("id", str(uuid.uuid4())),
                "type": "tool_error",
                "tool_name": tool_name,
                "error": error_pdu_content,
                "context": mcp_pdu.get("context", {})
            }
            return JSONResponse({"jsonrpc": "2.0", "result": response_mcp_pdu, "id": json_rpc_id}, status_code=200) # JSON-RPC spec: result is for successful app-level outcomes, error for JSON-RPC errors. MCP error is an app-level outcome.

    except json.JSONDecodeError:
        return JSONResponse({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}, status_code=400)
    except Exception as e:
        logger.error(f"Unexpected error in handle_direct_tool_call: {e}", exc_info=True)
        return JSONResponse({"jsonrpc": "2.0", "error": {"code": -32603, "message": "Internal error"}, "id": None}, status_code=500)

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
def run_command_tool(command: str, session_id: Optional[str] = None, cwd: Optional[str] = None, timeout: int = 60, requires_approval: bool = True) -> dict:
    # Log context, including correlation_id if present
    # Assuming context is passed or can be accessed if FastMCP supports it here.
    # For now, just log parameters that are directly passed.
    logger.info(f"run_command_tool invoked with command: '{command}', session_id: '{session_id}', cwd: '{cwd}', timeout: {timeout}, approval: {requires_approval}")

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

@mcp_server.tool("linux.sshExecuteCommand")
async def ssh_execute_command(target_host: str, remote_command: str) -> Dict[str, Any]:
    """
    Executes a command on a remote Linux host via SSH.
    The target_host must be pre-configured in the SSH_HOSTS environment variable.
    """
    logger.info(f"Attempting SSH command on {target_host}: {remote_command}")

    if not SSH_HOSTS_STR:
        logger.error("SSH_HOSTS environment variable not set. Cannot execute SSH command.")
        return {"error": "SSH is not configured on the server: SSH_HOSTS not set."}

    if target_host not in SSH_CONFIG:
        logger.error(f"Host '{target_host}' is not a configured SSH target. Available: {list(SSH_CONFIG.keys())}")
        return {"error": f"Host '{target_host}' is not a configured SSH target."}

    host_config = SSH_CONFIG[target_host]
    ssh_user = host_config["user"]
    ssh_key_file = host_config["key_path"]

    if not os.path.exists(ssh_key_file):
        logger.error(f"SSH key file not found at {ssh_key_file} for host {target_host}")
        return {"error": f"SSH key file not found at {ssh_key_file} for host {target_host}"}
    
    # Validate the remote_command (basic validation for now, can be expanded)
    # This is a tricky part, as remote commands can also be dangerous.
    # For now, we rely on the restricted SSH key and user permissions on the target.
    # A more robust solution might involve a predefined set of allowed remote commands or patterns.
    if not remote_command or any(char in remote_command for char in ['\\n', ';', '&&', '||', '`', '$(']):
        logger.warning(f"Potentially unsafe characters in remote command for SSH: {remote_command}")
        return {"error": "Invalid or potentially unsafe remote command."}

    # Construct the SSH command
    # -o StrictHostKeyChecking=no and UserKnownHostsFile=/dev/null are used to avoid issues with host key verification in a containerized environment.
    # This has security implications if the network can be MITM'd. For controlled environments.
    # For higher security, manage known_hosts.
    ssh_command_list = [
        "ssh",
        "-i", ssh_key_file,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        f"{ssh_user}@{target_host}",
        remote_command
    ]
    
    command_str_for_log = ' '.join(shlex.quote(arg) for arg in ssh_command_list)
    logger.info(f"Executing SSH command: {command_str_for_log}")

    try:
        process = subprocess.run(
            ssh_command_list,
            capture_output=True,
            text=True,
            check=False, # Don't raise exception for non-zero exit codes, handle it in result
            timeout=60  # Timeout for the SSH command
        )
        logger.info(f"SSH command to {target_host} exited with code {process.returncode}")
        return {
            "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip(),
            "exit_code": process.returncode,
            "command_executed": command_str_for_log
        }
    except subprocess.TimeoutExpired:
        logger.error(f"SSH command to {target_host} timed out: {command_str_for_log}")
        return {"error": "SSH command timed out", "stdout": "", "stderr": "Timeout after 60 seconds."}
    except Exception as e:
        logger.error(f"Error executing SSH command to {target_host}: {e}", exc_info=True)
        return {"error": str(e), "stdout": "", "stderr": str(e)}

# --- Main Execution ---
if __name__ == "__main__":
    logger.info(f"Starting Linux CLI MCP Server on port {MCP_PORT} using explicit SseServerTransport setup.")
    
    # Create the Starlette app using the helper function
    # This app is configured with /sse (GET), /messages (POST), and /health (GET)
    app = create_sse_application(mcp_server)

    # Retrieve host and log_level from the FastMCP instance (mcp_server)
    # These are typically set in the FastMCP constructor or have defaults.
    # Fallback to defaults if attributes are somehow not present.
    host_to_run = getattr(mcp_server, 'host', "0.0.0.0")
    log_level_setting = getattr(mcp_server, 'log_level', "INFO") # FastMCP defaults log_level to "INFO"

    # Uvicorn expects the log level string to be lowercase.
    uvicorn_log_level = log_level_setting.lower()

    # Diagnostic: Log the keys in the internal tools dictionary
    if hasattr(mcp_server, '_mcp_server') and hasattr(mcp_server._mcp_server, 'tools'):
        logger.info(f"Available tool keys in mcp_server._mcp_server.tools: {list(mcp_server._mcp_server.tools.keys())}")
    else:
        logger.warning("Could not access mcp_server._mcp_server.tools for diagnostics.")

    logger.info(f"Attempting to run Uvicorn with Starlette app, host: {host_to_run}, port: {MCP_PORT}, log_level: {uvicorn_log_level}")
    try:
        uvicorn.run(app, host=host_to_run, port=MCP_PORT, log_level=uvicorn_log_level)
    except Exception as e:
        # Log the exception with its type and message
        logger.critical(f"Linux CLI MCP Server (Uvicorn explicit run) failed: {type(e).__name__} - {e}", exc_info=True)
        # Ensure a non-zero exit code on critical failure
        import sys
        sys.exit(1) 
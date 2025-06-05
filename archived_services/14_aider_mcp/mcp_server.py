#!/usr/bin/env python3
"""
Aider MCP Server - Provides AI coding assistance through Aider
"""
import os
import sys
import logging
import subprocess
import json
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime as dt

from fastmcp import FastMCP
from starlette.routing import Route
from starlette.responses import JSONResponse
import uvicorn

# JSON Formatter for logging
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
        return json.dumps(log_entry)

# Logging setup
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

SERVICE_NAME = "aider-mcp"
json_formatter = JSONFormatter(SERVICE_NAME)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(json_formatter)
root_logger.addHandler(stream_handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

# Configuration
MCP_PORT = int(os.getenv("MCP_PORT", 8014))
REPO_PATH = os.getenv("REPO_PATH", "/workspace")

# Initialize FastMCP server
mcp_server = FastMCP(name="aider-service", port=MCP_PORT, host="0.0.0.0")

# Health check endpoint
async def health_check(request):
    return JSONResponse({
        "status": "healthy", 
        "service": SERVICE_NAME, 
        "timestamp": dt.now().timestamp(),
        "aider_available": check_aider_available()
    })

def check_aider_available():
    """Check if aider is installed and available"""
    try:
        result = subprocess.run(["aider", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

@mcp_server.tool("aider.chat")
def aider_chat(prompt: str, files: Optional[List[str]] = None, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Run an Aider chat session with the given prompt.
    
    Args:
        prompt: The instruction or question for Aider
        files: Optional list of file paths to include in the chat
        model: Optional model to use (e.g., 'gpt-4', 'claude-3-opus')
    
    Returns:
        Result of the Aider operation
    """
    logger.info(f"Aider chat requested: {prompt[:100]}...")
    
    try:
        cmd = ["aider", "--no-auto-commits", "--yes"]
        
        # Add model if specified
        if model:
            cmd.extend(["--model", model])
        
        # Add files if specified
        if files:
            for file in files:
                file_path = Path(REPO_PATH) / file
                if file_path.exists():
                    cmd.append(str(file_path))
                else:
                    logger.warning(f"File not found: {file_path}")
        
        # Create a temporary file with the prompt
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(prompt)
            prompt_file = f.name
        
        # Run aider with the prompt
        cmd.extend(["--message-file", prompt_file])
        
        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            cwd=REPO_PATH,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Clean up temp file
        os.unlink(prompt_file)
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        logger.error("Aider command timed out")
        return {"success": False, "error": "Command timed out after 5 minutes"}
    except Exception as e:
        logger.error(f"Error running Aider: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

@mcp_server.tool("aider.architect")
def aider_architect(description: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Use Aider in architect mode to plan changes without making them.
    
    Args:
        description: Description of the architecture or changes to plan
        files: Optional list of files to analyze
    
    Returns:
        Aider's architectural analysis and suggestions
    """
    logger.info("Aider architect mode requested")
    
    try:
        cmd = ["aider", "--architect", "--no-auto-commits"]
        
        if files:
            for file in files:
                file_path = Path(REPO_PATH) / file
                if file_path.exists():
                    cmd.append(str(file_path))
        
        # Create temp file with description
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(description)
            desc_file = f.name
        
        cmd.extend(["--message-file", desc_file])
        
        result = subprocess.run(
            cmd,
            cwd=REPO_PATH,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        os.unlink(desc_file)
        
        return {
            "success": result.returncode == 0,
            "analysis": result.stdout,
            "stderr": result.stderr
        }
        
    except Exception as e:
        logger.error(f"Error in architect mode: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

@mcp_server.tool("aider.ask")
def aider_ask(question: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Ask Aider a question about the codebase without making changes.
    
    Args:
        question: The question to ask about the code
        files: Optional list of files to include in context
    
    Returns:
        Aider's answer to the question
    """
    logger.info(f"Aider question: {question[:100]}...")
    
    try:
        cmd = ["aider", "--ask", "--no-auto-commits"]
        
        if files:
            for file in files:
                file_path = Path(REPO_PATH) / file
                if file_path.exists():
                    cmd.append(str(file_path))
        
        # Use stdin for the question
        result = subprocess.run(
            cmd,
            cwd=REPO_PATH,
            input=question,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        return {
            "success": result.returncode == 0,
            "answer": result.stdout,
            "stderr": result.stderr
        }
        
    except Exception as e:
        logger.error(f"Error asking Aider: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

@mcp_server.resource("aider://status")
def get_aider_status():
    """Get the current status of Aider and available models"""
    try:
        # Check Aider version
        version_result = subprocess.run(
            ["aider", "--version"],
            capture_output=True,
            text=True
        )
        
        # Check available models
        models_result = subprocess.run(
            ["aider", "--models"],
            capture_output=True,
            text=True
        )
        
        return {
            "installed": version_result.returncode == 0,
            "version": version_result.stdout.strip() if version_result.returncode == 0 else "Not installed",
            "available_models": models_result.stdout if models_result.returncode == 0 else "Could not retrieve models",
            "repo_path": REPO_PATH,
            "repo_exists": os.path.exists(REPO_PATH)
        }
    except Exception as e:
        return {
            "installed": False,
            "error": str(e)
        }

# Main execution
if __name__ == "__main__":
    logger.info(f"Starting Aider MCP Server on port {MCP_PORT}")
    
    # Get the SSE app from FastMCP
    app = mcp_server.sse_app()
    
    # Add health check route
    if not any(r.path == "/health" for r in getattr(app, 'routes', [])):
        if hasattr(app, 'routes') and isinstance(app.routes, list):
            app.routes.append(Route("/health", health_check))
            logger.info("Health check route added")
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT, log_level="info")
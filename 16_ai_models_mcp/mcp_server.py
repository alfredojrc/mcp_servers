import os
import logging
import json
from datetime import datetime as dt
from typing import Optional, List, Dict, Any, Literal

from fastmcp import FastMCP
from starlette.routing import Route
from starlette.responses import JSONResponse
import uvicorn

# LLM SDKs
import google.generativeai as genai
from anthropic import Anthropic, AnthropicError

# --- JSON Formatter Class (Standard) ---
SERVICE_NAME_FOR_LOGGING = "ai-models-mcp"

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
        if hasattr(record, 'props') and record.props:
            log_entry['props'] = record.props
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        if record.stack_info:
            log_entry['stack_info'] = self.formatStack(record.stack_info)
        return json.dumps(log_entry)

# --- Logging Setup (Standard) ---
logger = logging.getLogger(__name__)
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)
json_formatter = JSONFormatter(SERVICE_NAME_FOR_LOGGING)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(json_formatter)
root_logger.addHandler(stream_handler)
root_logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())


# --- Configuration ---
MCP_PORT = int(os.getenv("MCP_PORT", "8016"))

# API Key Configuration (Paths to Docker Secrets)
GEMINI_API_KEY_SECRET_PATH = os.getenv("GEMINI_API_KEY_SECRET_PATH", "/run/secrets/gemini_api_key")
ANTHROPIC_API_KEY_SECRET_PATH = os.getenv("ANTHROPIC_API_KEY_SECRET_PATH", "/run/secrets/anthropic_api_key")

# Load API keys from secret files
GEMINI_API_KEY = None
if os.path.exists(GEMINI_API_KEY_SECRET_PATH):
    with open(GEMINI_API_KEY_SECRET_PATH, 'r') as f:
        GEMINI_API_KEY = f.read().strip()
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        logger.info("Gemini API Key loaded and configured.")
    else:
        logger.warning("Gemini API Key file found but is empty.")
else:
    logger.warning(f"Gemini API Key secret file not found at {GEMINI_API_KEY_SECRET_PATH}")

ANTHROPIC_API_KEY = None
if os.path.exists(ANTHROPIC_API_KEY_SECRET_PATH):
    with open(ANTHROPIC_API_KEY_SECRET_PATH, 'r') as f:
        ANTHROPIC_API_KEY = f.read().strip()
    if ANTHROPIC_API_KEY:
        anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
        logger.info("Anthropic API Key loaded and client initialized.")
    else:
        anthropic_client = None
        logger.warning("Anthropic API Key file found but is empty.")
else:
    anthropic_client = None
    logger.warning(f"Anthropic API Key secret file not found at {ANTHROPIC_API_KEY_SECRET_PATH}")


# --- FastMCP Server Setup ---
mcp_server = FastMCP(name="ai-models-mcp", port=MCP_PORT, host="0.0.0.0")

# --- Tool Definitions ---

@mcp_server.tool("ai.models.gemini.generateContent")
def gemini_generate_content(
    prompt: str,
    model_name: str = "gemini-1.5-flash-latest",
    temperature: Optional[float] = None,
    max_output_tokens: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate content using Gemini models.
    
    Args:
        prompt: The text prompt to send to the model.
        model_name: The Gemini model to use (e.g., 'gemini-1.5-flash-latest', 'gemini-pro').
        temperature: Controls randomness in generation (0.0 to 1.0).
        max_output_tokens: Maximum number of tokens to generate.
    
    Returns:
        Generated text or error message.
    """
    if not GEMINI_API_KEY:
        logger.error("Gemini API Key not configured.")
        return {"error": "Gemini API Key not configured. Cannot call Gemini models."}
    
    try:
        # Configure generation settings
        generation_config = {}
        if temperature is not None:
            generation_config["temperature"] = temperature
        if max_output_tokens is not None:
            generation_config["max_output_tokens"] = max_output_tokens
        
        # Initialize model
        model = genai.GenerativeModel(model_name)
        
        # Generate content
        response = model.generate_content(
            prompt,
            generation_config=generation_config if generation_config else None
        )
        
        logger.info(f"Gemini content generated successfully with model: {model_name}",
                   extra={"props": {"model": model_name, "prompt_length": len(prompt)}})
        
        return {
            "model": model_name,
            "generated_text": response.text,
            "prompt_tokens": None,  # Gemini doesn't provide token counts in the same way
            "completion_tokens": None,
            "total_tokens": None
        }
        
    except Exception as e:
        logger.error(f"Error generating content with Gemini: {e}", exc_info=True)
        return {"error": f"Error generating content: {str(e)}"}

@mcp_server.tool("ai.models.anthropic.createMessage")
def anthropic_create_message(
    prompt: str,
    model: str = "claude-3-haiku-20240307",
    max_tokens: int = 1024,
    temperature: Optional[float] = None,
    system: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a message using Anthropic's Claude models.
    
    Args:
        prompt: The user message to send to Claude.
        model: The Claude model to use (e.g., 'claude-3-haiku-20240307', 'claude-3-5-sonnet-20241022').
        max_tokens: Maximum number of tokens to generate.
        temperature: Controls randomness in generation (0.0 to 1.0).
        system: Optional system message to set context.
    
    Returns:
        Generated message or error.
    """
    if not anthropic_client:
        logger.error("Anthropic client not initialized.")
        return {"error": "Anthropic API Key not configured. Cannot call Claude models."}
    
    try:
        # Build message
        messages = [{"role": "user", "content": prompt}]
        
        # Create request parameters
        params = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages
        }
        
        if temperature is not None:
            params["temperature"] = temperature
        if system:
            params["system"] = system
        
        # Create message
        response = anthropic_client.messages.create(**params)
        
        logger.info(f"Anthropic message created successfully with model: {model}",
                   extra={"props": {"model": model, "prompt_length": len(prompt)}})
        
        return {
            "model": model,
            "response": response.content[0].text if response.content else "",
            "input_tokens": response.usage.input_tokens if hasattr(response, 'usage') else None,
            "output_tokens": response.usage.output_tokens if hasattr(response, 'usage') else None,
            "stop_reason": response.stop_reason if hasattr(response, 'stop_reason') else None
        }
        
    except AnthropicError as e:
        logger.error(f"Anthropic API error: {e}", exc_info=True)
        return {"error": f"Anthropic API error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error creating message with Anthropic: {e}", exc_info=True)
        return {"error": f"Error creating message: {str(e)}"}

@mcp_server.tool("ai.models.listAvailable")
def list_available_models() -> Dict[str, Any]:
    """
    List available AI models and their status.
    
    Returns:
        Dictionary of available models and their configuration status.
    """
    available_models = {
        "gemini": {
            "configured": bool(GEMINI_API_KEY),
            "models": [
                "gemini-1.5-flash-latest",
                "gemini-1.5-flash",
                "gemini-1.5-pro-latest", 
                "gemini-1.5-pro",
                "gemini-pro"
            ] if GEMINI_API_KEY else []
        },
        "anthropic": {
            "configured": bool(anthropic_client),
            "models": [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307"
            ] if anthropic_client else []
        }
    }
    
    logger.info("Listed available models",
               extra={"props": {"gemini_configured": available_models["gemini"]["configured"],
                               "anthropic_configured": available_models["anthropic"]["configured"]}})
    
    return available_models

# --- Health Check Endpoint ---
async def health_check(request):
    gemini_status = "configured" if GEMINI_API_KEY else "not_configured"
    anthropic_status = "configured" if anthropic_client else "not_configured"
    
    return JSONResponse({
        "status": "healthy",
        "service": SERVICE_NAME_FOR_LOGGING,
        "timestamp": dt.now().isoformat(),
        "models": {
            "gemini": gemini_status,
            "anthropic": anthropic_status
        }
    })

# --- Main Execution ---
if __name__ == "__main__":
    logger.info(f"Starting {SERVICE_NAME_FOR_LOGGING} on port {MCP_PORT}")
    
    # Get the SSE app from FastMCP
    app = mcp_server.sse_app()
    
    # Add health check route
    if not any(r.path == "/health" for r in getattr(app, 'routes', [])):
        if hasattr(app, 'routes') and isinstance(app.routes, list):
            app.routes.append(Route("/health", health_check))
            logger.info("Health check route added")
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT, log_level="info")
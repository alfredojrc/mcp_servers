import os
import logging
import json
from datetime import datetime as dt
from typing import Optional, List, Dict, Any, Literal

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
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
from fastmcp import FastMCP, Tool, ToolContext

app = FastMCP(
    title="AI Models MCP",
    description="Provides tools to interact with various Large Language Models (LLMs) like Gemini and Anthropic.",
    version="0.1.0",
    service_name=SERVICE_NAME_FOR_LOGGING,
)

# --- Model Parameters ---

class GeminiGenerateContentParams(BaseModel):
    model_name: str = Field(default="gemini-1.5-flash-latest", description="The Gemini model to use (e.g., 'gemini-1.5-flash-latest', 'gemini-pro').")
    prompt: str = Field(..., description="The text prompt to send to the model.")
    temperature: Optional[float] = Field(default=None, description="Controls randomness. Lower for more predictable, higher for more creative.")
    max_output_tokens: Optional[int] = Field(default=None, description="Maximum number of tokens to generate.")

class AnthropicCreateMessageParams(BaseModel):
    model_name: str = Field(default="claude-3-haiku-20240307", description="The Anthropic model to use (e.g., 'claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307').")
    system_prompt: Optional[str] = Field(default=None, description="System prompt to guide the model's behavior.")
    messages: List[Dict[str, str]] = Field(..., description="A list of message objects, e.g., [{'role': 'user', 'content': 'Hello'}].")
    max_tokens: int = Field(default=1024, description="Maximum number of tokens to generate in the response.")
    temperature: Optional[float] = Field(default=None, description="Controls randomness. Between 0.0 and 1.0.")

# --- AI Model Tools ---

@app.tool()
class GeminiGenerateContent(Tool[GeminiGenerateContentParams, Dict[str, Any]]):
    """Generates content using a specified Google Gemini model."""
    name = "ai.models.gemini.generateContent"
    description = "Generates text content using Google's Gemini models."

    async def run(self, context: ToolContext, params: GeminiGenerateContentParams) -> Dict[str, Any]:
        if not GEMINI_API_KEY:
            logger.error("Gemini API key not configured.")
            raise HTTPException(status_code=500, detail="Gemini API key not configured on the server.")
        
        try:
            logger.info(f"Calling Gemini model {params.model_name} with prompt starting: {params.prompt[:100]}...", 
                        extra={"props": {"model": params.model_name}})
            model = genai.GenerativeModel(params.model_name)
            generation_config = {}
            if params.temperature is not None:
                generation_config['temperature'] = params.temperature
            if params.max_output_tokens is not None:
                generation_config['max_output_tokens'] = params.max_output_tokens
            
            response = await model.generate_content_async(params.prompt, generation_config=generation_config if generation_config else None)
            
            generated_text = response.text
            logger.info(f"Gemini ({params.model_name}) generated response successfully.")
            return {"model": params.model_name, "generated_text": generated_text, "finish_reason": str(response.candidates[0].finish_reason) if response.candidates else None}
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error calling Gemini API: {str(e)}")

@app.tool()
class AnthropicCreateMessage(Tool[AnthropicCreateMessageParams, Dict[str, Any]]):
    """Creates a message using a specified Anthropic Claude model."""
    name = "ai.models.anthropic.createMessage"
    description = "Sends a message to Anthropic's Claude models and gets a response."

    async def run(self, context: ToolContext, params: AnthropicCreateMessageParams) -> Dict[str, Any]:
        if not anthropic_client:
            logger.error("Anthropic API key not configured or client not initialized.")
            raise HTTPException(status_code=500, detail="Anthropic API key not configured or client not initialized on the server.")
        
        try:
            logger.info(f"Calling Anthropic model {params.model_name} with messages: {params.messages}", 
                        extra={"props": {"model": params.model_name}})
            
            api_params = {
                "model": params.model_name,
                "max_tokens": params.max_tokens,
                "messages": params.messages,
            }
            if params.system_prompt:
                api_params["system"] = params.system_prompt
            if params.temperature is not None:
                api_params["temperature"] = params.temperature

            response = anthropic_client.messages.create(**api_params)
            
            response_content = ""
            if response.content and isinstance(response.content, list):
                for block in response.content:
                    if hasattr(block, 'text'):
                        response_content += block.text
            
            logger.info(f"Anthropic ({params.model_name}) generated response successfully.")
            return {
                "model": params.model_name, 
                "response_id": response.id, 
                "role": response.role,
                "content": response_content,
                "stop_reason": response.stop_reason,
                "usage": {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}
            }
        except AnthropicError as e:
            logger.error(f"Error calling Anthropic API: {e}", exc_info=True)
            raise HTTPException(status_code=e.status_code if hasattr(e, 'status_code') else 500, detail=f"Anthropic API Error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling Anthropic API: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Unexpected error calling Anthropic API: {str(e)}")

# --- Health Check (Standard) ---
@app.get("/health")
async def health_check():
    logger.debug("Health check requested")
    # Check if API keys are at least found (doesn't validate them)
    gemini_configured = bool(GEMINI_API_KEY)
    anthropic_configured = bool(ANTHROPIC_API_KEY and anthropic_client)
    
    status = "healthy"
    if not gemini_configured and not anthropic_configured:
        status = "unhealthy" # Or "degraded" if some functionality is still possible
    elif not gemini_configured or not anthropic_configured:
        status = "degraded"
        
    return {
        "status": status, 
        "service": SERVICE_NAME_FOR_LOGGING, 
        "timestamp": dt.now().isoformat(),
        "checks": {
            "gemini_api_key_found": gemini_configured,
            "anthropic_api_key_found": anthropic_configured
        }
    }

if __name__ == "__main__":
    log_level_env = os.getenv("LOG_LEVEL", "INFO").lower()
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT, log_level=log_level_env) 
import os
from fastmcp import FastMCP
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
import asyncio
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mcp_host")

# Get port from environment variable or use 8000 as default
MCP_PORT = int(os.getenv("MCP_PORT", 8000))

# Create a simple web interface
async def homepage(request):
    return HTMLResponse("""
    <html>
        <head>
            <title>MCP Host Server</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                h1 { color: #333; }
                .container { max-width: 800px; margin: 0 auto; }
                .info { background-color: #f5f5f5; padding: 20px; border-radius: 5px; }
                code { background-color: #eee; padding: 2px 5px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>MCP Host Server</h1>
                <div class="info">
                    <p>This server is running the Model Context Protocol (MCP) service.</p>
                    <p>Status: <strong>Running</strong></p>
                    <p>Port: <strong>""" + str(MCP_PORT) + """</strong></p>
                </div>
                <h2>Available Tools</h2>
                <ul>
                    <li><code>hello_world</code> - A simple greeting tool</li>
                    <li><code>add_numbers</code> - Adds two numbers together</li>
                    <li><code>get_server_info</code> - Returns server information</li>
                </ul>
                <h2>API Endpoints</h2>
                <ul>
                    <li><a href="/api/status">/api/status</a> - Server status information</li>
                </ul>
                <h2>MCP Endpoints</h2>
                <ul>
                    <li><code>/mcp</code> - MCP endpoint (supports both JSON-RPC and SSE)</li>
                    <li><code>/mcp/sse</code> - MCP SSE-specific stream endpoint</li>
                </ul>
            </div>
        </body>
    </html>
    """)

async def status(request):
    return JSONResponse({
        "status": "online",
        "service": "MCP Host",
        "port": MCP_PORT,
        "version": "1.0.0"
    })

# Create a middleware for request logging
class LoggingMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            logger.debug(f"Request: {scope['method']} {scope['path']}")
            
            # Modified send to log responses
            async def send_with_logging(message):
                if message["type"] == "http.response.start":
                    logger.debug(f"Response status: {message['status']}")
                await send(message)
            
            await self.app(scope, receive, send_with_logging)
        else:
            await self.app(scope, receive, send)

# Create our web app
web_app = Starlette(
    routes=[
        Route("/", homepage),
        Route("/api/status", status),
    ],
    middleware=[
        Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    ]
)

# Create the master orchestrator server with a name and description
mcp = FastMCP(
    name="Master Orchestrator", 
    instructions="MCP Host server that coordinates MCP services",
    host="0.0.0.0",  # Bind to all interfaces
    port=MCP_PORT
)

# Enable debugging
mcp.settings.debug = True

# Create simple MCP tool functions
@mcp.tool()
def hello_world(name="World"):
    """A simple hello world tool for testing"""
    return f"Hello, {name}!"

@mcp.tool()
def add_numbers(a: int, b: int):
    """Add two numbers together"""
    return a + b

@mcp.tool()
def get_server_info():
    """Get information about the MCP server"""
    return {
        "name": "Master Orchestrator",
        "version": "1.0.0",
        "port": MCP_PORT
    }

# Resource example
@mcp.resource("orchestrator://status")
def server_status():
    """Get the current server status"""
    return {
        "status": "online",
        "service": "MCP Host",
        "port": MCP_PORT,
        "version": "1.0.0"
    }

# Example of a prompt template
@mcp.prompt()
def greeting_prompt(user_name: str):
    """Returns a greeting prompt template"""
    return f"Hello {user_name}, I'm the MCP Host server. How can I help you today?"

# TODO: Mount sub-servers or add proxy logic here if needed
# Example:
# from linux_cli_mcp import mcp as linux_mcp
# mcp.mount("linux", linux_mcp)

# Customize the MCP server settings
mcp.settings.sse_path = "/sse"  # Relative path within the mount
mcp.settings.message_path = "/"  # Relative path within the mount

# Get the MCP app
mcp_app = mcp.sse_app()

# Combined app
app = Starlette(
    routes=[
        Mount("/mcp", mcp_app),  # Mount the MCP app at /mcp
        Mount("/api", routes=[
            Route("/status", status, methods=["GET"])
        ]),
        Route("/", homepage)
    ],
    middleware=[
        Middleware(LoggingMiddleware),  # Add logging middleware
        Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    ]
)

if __name__ == "__main__":
    print(f"Starting MCP Host (mounted) on port {MCP_PORT}...")
    # Run the server with the combined app
    uvicorn_config = uvicorn.Config(app=app, host="0.0.0.0", port=MCP_PORT, log_level="debug")
    server = uvicorn.Server(uvicorn_config)
    server.run() 
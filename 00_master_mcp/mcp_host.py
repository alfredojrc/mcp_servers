import os
from mcp.server.fastmcp import FastMCP
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import HTMLResponse, JSONResponse
import asyncio
import threading

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
                <h2>API Endpoints</h2>
                <ul>
                    <li><a href="/api/status">/api/status</a> - Server status information</li>
                </ul>
            </div>
        </body>
    </html>
    """)

async def status(request):
    return JSONResponse({
        "status": "online",
        "service": "MCP Host",
        "port": MCP_PORT
    })

# Create the Starlette app for web interface
routes = [
    Route("/", homepage),
    Route("/api/status", status)
]

# Create the master orchestrator server
mcp = FastMCP("Master Orchestrator", port=MCP_PORT)

# TODO: Mount sub-servers or add proxy logic here if needed
# Example:
# from linux_cli_mcp import mcp as linux_mcp
# mcp.mount("linux", linux_mcp)

def run_mcp():
    print(f"Starting MCP Host on port {MCP_PORT}...")
    mcp.run(transport='sse')  # Use SSE transport which enables web interface

if __name__ == "__main__":
    print(f"Starting MCP Host on port {MCP_PORT}...")
    
    # Get the Starlette app from FastMCP
    app = mcp.sse_app()
    
    # Add our routes to the existing app
    for route in routes:
        app.routes.append(route)
    
    # Run the server with Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT) 
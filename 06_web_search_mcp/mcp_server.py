import os
import logging
from typing import Optional, List, Dict, Any
import json
from datetime import datetime as dt
import httpx
import asyncio

from mcp.server.fastmcp import FastMCP
from starlette.routing import Route
from starlette.responses import JSONResponse

# Try to import search libraries
try:
    from duckduckgo_search import DDGS
except ImportError:
    DDGS = None

# JSON Formatter Class
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

# Logging Setup
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

SERVICE_NAME = "web-search-service"
json_formatter = JSONFormatter(SERVICE_NAME)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(json_formatter)
root_logger.addHandler(stream_handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

# Configuration
MCP_PORT = int(os.getenv("MCP_PORT", 8006))

# Metrics tracking
metrics = {
    "searches_performed": 0,
    "searches_by_engine": {},
    "errors": 0,
    "last_search_time": None
}

# Initialize FastMCP
mcp = FastMCP("Web Search MCP Server")

@mcp.tool("web.search.query")
async def search_query(
    query: str,
    engine: str = "duckduckgo",
    max_results: int = 5
) -> Dict[str, Any]:
    """
    Perform a web search using the specified engine.
    
    Args:
        query: The search query string
        engine: Search engine to use (currently only 'duckduckgo' is implemented)
        max_results: Maximum number of results to return (default: 5)
        
    Returns:
        Dictionary containing search results with title, link, and snippet
    """
    global metrics
    
    logger.info(f"Performing search with engine={engine}, query='{query}', max_results={max_results}")
    
    try:
        results = []
        
        if engine.lower() == "duckduckgo":
            if not DDGS:
                error_msg = "DuckDuckGo search library not installed"
                logger.error(error_msg)
                metrics["errors"] += 1
                return {"error": error_msg, "results": []}
            
            try:
                with DDGS() as ddgs:
                    search_results = list(ddgs.text(query, max_results=max_results))
                    
                for result in search_results:
                    results.append({
                        "title": result.get("title", ""),
                        "link": result.get("link", ""),
                        "snippet": result.get("body", "")
                    })
                    
            except Exception as e:
                logger.error(f"DuckDuckGo search error: {str(e)}")
                metrics["errors"] += 1
                return {"error": f"Search failed: {str(e)}", "results": []}
                
        else:
            error_msg = f"Search engine '{engine}' not implemented. Available: duckduckgo"
            logger.warning(error_msg)
            return {"error": error_msg, "results": []}
        
        # Update metrics
        metrics["searches_performed"] += 1
        metrics["searches_by_engine"][engine] = metrics["searches_by_engine"].get(engine, 0) + 1
        metrics["last_search_time"] = dt.now().isoformat()
        
        logger.info(f"Search completed successfully, found {len(results)} results")
        
        return {
            "query": query,
            "engine": engine,
            "results_count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in search: {str(e)}", exc_info=True)
        metrics["errors"] += 1
        return {"error": f"Unexpected error: {str(e)}", "results": []}

@mcp.tool("web.search.getMetrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get metrics about web search operations.
    
    Returns:
        Dictionary containing search metrics
    """
    return {
        "service": SERVICE_NAME,
        "metrics": metrics,
        "timestamp": dt.now().isoformat()
    }

@mcp.tool("web.search.listEngines")
async def list_engines() -> Dict[str, Any]:
    """
    List available search engines and their status.
    
    Returns:
        Dictionary containing available search engines
    """
    engines = {
        "duckduckgo": {
            "available": DDGS is not None,
            "description": "DuckDuckGo search (no API key required)",
            "status": "active" if DDGS else "library not installed"
        },
        "google": {
            "available": False,
            "description": "Google Custom Search (requires API key)",
            "status": "not implemented"
        },
        "bing": {
            "available": False,
            "description": "Bing Web Search (requires API key)",
            "status": "not implemented"
        }
    }
    
    return {
        "engines": engines,
        "default": "duckduckgo"
    }

# Startup message
logger.info(f"Web Search MCP Server starting on port {MCP_PORT}")
logger.info(f"Available search engines: DuckDuckGo={'available' if DDGS else 'not available'}")
if not DDGS:
    logger.warning("Install duckduckgo-search for search functionality: pip install duckduckgo-search")

if __name__ == "__main__":
    # Run the FastMCP server
    mcp.run(host="0.0.0.0", port=MCP_PORT)
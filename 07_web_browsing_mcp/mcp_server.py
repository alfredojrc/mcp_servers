import os
import logging
from typing import Optional, Dict, Any
import json
from datetime import datetime as dt
import asyncio
import base64

from mcp.server.fastmcp import FastMCP

# Try to import browser automation libraries
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

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

SERVICE_NAME = "web-browsing-service"
json_formatter = JSONFormatter(SERVICE_NAME)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(json_formatter)
root_logger.addHandler(stream_handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

# Configuration
MCP_PORT = int(os.getenv("MCP_PORT", 8007))
BROWSER_TYPE = os.getenv("BROWSER_TYPE", "chromium")

# Browser instance management
browser = None
context = None
page = None
playwright = None

# Metrics tracking
metrics = {
    "pages_loaded": 0,
    "actions_performed": 0,
    "screenshots_taken": 0,
    "errors": 0,
    "last_url": None
}

# Initialize FastMCP
mcp = FastMCP("Web Browsing MCP Server")

async def ensure_browser():
    """Ensure browser is initialized"""
    global browser, context, page, playwright
    
    if not PLAYWRIGHT_AVAILABLE:
        raise Exception("Playwright is not installed. Install with: pip install playwright && playwright install chromium")
    
    if not browser:
        logger.info(f"Initializing {BROWSER_TYPE} browser")
        playwright = await async_playwright().start()
        browser = await getattr(playwright, BROWSER_TYPE).launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = await browser.new_context()
        page = await context.new_page()
        logger.info("Browser initialized successfully")
    
    return page

@mcp.tool("web.browse.navigation.navigateTo")
async def navigate_to(url: str) -> Dict[str, Any]:
    """
    Navigate the browser to a specific URL.
    
    Args:
        url: The URL to navigate to
        
    Returns:
        Dictionary with navigation result
    """
    try:
        page = await ensure_browser()
        logger.info(f"Navigating to: {url}")
        
        await page.goto(url, wait_until="networkidle")
        
        metrics["pages_loaded"] += 1
        metrics["last_url"] = url
        
        return {
            "success": True,
            "url": page.url,
            "title": await page.title(),
            "status": "loaded"
        }
    except Exception as e:
        logger.error(f"Navigation error: {str(e)}")
        metrics["errors"] += 1
        return {"error": str(e), "success": False}

@mcp.tool("web.browse.navigation.getCurrentUrl")
async def get_current_url() -> Dict[str, Any]:
    """
    Get the current URL of the browser.
    
    Returns:
        Dictionary with current URL information
    """
    try:
        page = await ensure_browser()
        return {
            "url": page.url,
            "title": await page.title()
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool("web.browse.navigation.goBack")
async def go_back() -> Dict[str, Any]:
    """Navigate back in browser history."""
    try:
        page = await ensure_browser()
        await page.go_back()
        return {
            "success": True,
            "url": page.url,
            "title": await page.title()
        }
    except Exception as e:
        return {"error": str(e), "success": False}

@mcp.tool("web.browse.navigation.goForward")
async def go_forward() -> Dict[str, Any]:
    """Navigate forward in browser history."""
    try:
        page = await ensure_browser()
        await page.go_forward()
        return {
            "success": True,
            "url": page.url,
            "title": await page.title()
        }
    except Exception as e:
        return {"error": str(e), "success": False}

@mcp.tool("web.browse.extraction.getPageContent")
async def get_page_content(format: str = "text") -> Dict[str, Any]:
    """
    Extract the page content in specified format.
    
    Args:
        format: Output format - 'text' or 'html'
        
    Returns:
        Dictionary with page content
    """
    try:
        page = await ensure_browser()
        
        if format == "html":
            content = await page.content()
        else:  # default to text
            content = await page.inner_text("body")
        
        return {
            "format": format,
            "content": content,
            "url": page.url,
            "length": len(content)
        }
    except Exception as e:
        logger.error(f"Content extraction error: {str(e)}")
        return {"error": str(e)}

@mcp.tool("web.browse.extraction.getElementText")
async def get_element_text(selector: str) -> Dict[str, Any]:
    """
    Get text content of a specific element.
    
    Args:
        selector: CSS selector for the element
        
    Returns:
        Dictionary with element text
    """
    try:
        page = await ensure_browser()
        element = await page.query_selector(selector)
        
        if not element:
            return {"error": f"Element not found: {selector}"}
        
        text = await element.inner_text()
        return {
            "selector": selector,
            "text": text,
            "length": len(text)
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool("web.browse.extraction.getScreenshot")
async def get_screenshot(selector: Optional[str] = None) -> Dict[str, Any]:
    """
    Take a screenshot of the page or specific element.
    
    Args:
        selector: Optional CSS selector for element screenshot
        
    Returns:
        Dictionary with base64 encoded screenshot
    """
    try:
        page = await ensure_browser()
        
        if selector:
            element = await page.query_selector(selector)
            if not element:
                return {"error": f"Element not found: {selector}"}
            screenshot_bytes = await element.screenshot()
        else:
            screenshot_bytes = await page.screenshot(full_page=True)
        
        metrics["screenshots_taken"] += 1
        
        return {
            "screenshot": base64.b64encode(screenshot_bytes).decode('utf-8'),
            "format": "base64",
            "type": "element" if selector else "full_page",
            "size": len(screenshot_bytes)
        }
    except Exception as e:
        logger.error(f"Screenshot error: {str(e)}")
        metrics["errors"] += 1
        return {"error": str(e)}

@mcp.tool("web.browse.interaction.clickElement")
async def click_element(selector: str, approval_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Click an element on the page (requires approval).
    
    Args:
        selector: CSS selector for the element to click
        approval_token: Token confirming approval for this action
        
    Returns:
        Dictionary with click result
    """
    if not approval_token:
        return {"error": "This action requires approval. Please provide approval_token."}
    
    try:
        page = await ensure_browser()
        element = await page.query_selector(selector)
        
        if not element:
            return {"error": f"Element not found: {selector}"}
        
        await element.click()
        metrics["actions_performed"] += 1
        
        logger.info(f"Clicked element: {selector}")
        
        return {
            "success": True,
            "selector": selector,
            "action": "click",
            "url": page.url
        }
    except Exception as e:
        logger.error(f"Click error: {str(e)}")
        metrics["errors"] += 1
        return {"error": str(e), "success": False}

@mcp.tool("web.browse.interaction.fillForm")
async def fill_form(selector: str, value: str, approval_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Fill a form field (requires approval).
    
    Args:
        selector: CSS selector for the form field
        value: Value to fill
        approval_token: Token confirming approval for this action
        
    Returns:
        Dictionary with fill result
    """
    if not approval_token:
        return {"error": "This action requires approval. Please provide approval_token."}
    
    try:
        page = await ensure_browser()
        element = await page.query_selector(selector)
        
        if not element:
            return {"error": f"Element not found: {selector}"}
        
        await element.fill(value)
        metrics["actions_performed"] += 1
        
        # Log with masked value for security
        masked_value = value[:2] + "*" * (len(value) - 4) + value[-2:] if len(value) > 4 else "*" * len(value)
        logger.info(f"Filled form field: {selector} with value: {masked_value}")
        
        return {
            "success": True,
            "selector": selector,
            "action": "fill",
            "value_length": len(value)
        }
    except Exception as e:
        logger.error(f"Form fill error: {str(e)}")
        metrics["errors"] += 1
        return {"error": str(e), "success": False}

@mcp.tool("web.browse.interaction.scrollPage")
async def scroll_page(direction: str = "down", amount: int = 500) -> Dict[str, Any]:
    """
    Scroll the page.
    
    Args:
        direction: Scroll direction ('up' or 'down')
        amount: Pixels to scroll
        
    Returns:
        Dictionary with scroll result
    """
    try:
        page = await ensure_browser()
        
        if direction == "down":
            await page.evaluate(f"window.scrollBy(0, {amount})")
        else:
            await page.evaluate(f"window.scrollBy(0, -{amount})")
        
        return {
            "success": True,
            "direction": direction,
            "amount": amount
        }
    except Exception as e:
        return {"error": str(e), "success": False}

@mcp.tool("web.browse.getMetrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get metrics about web browsing operations.
    
    Returns:
        Dictionary containing browsing metrics
    """
    return {
        "service": SERVICE_NAME,
        "metrics": metrics,
        "browser_active": browser is not None,
        "timestamp": dt.now().isoformat()
    }

# Cleanup on shutdown
async def cleanup():
    """Clean up browser resources"""
    global browser, context, page, playwright
    
    if page:
        await page.close()
    if context:
        await context.close()
    if browser:
        await browser.close()
    if playwright:
        await playwright.stop()
    
    logger.info("Browser resources cleaned up")

# Startup message
logger.info(f"Web Browsing MCP Server starting on port {MCP_PORT}")
logger.info(f"Browser type: {BROWSER_TYPE}")
logger.info(f"Playwright available: {PLAYWRIGHT_AVAILABLE}")

if not PLAYWRIGHT_AVAILABLE:
    logger.warning("Playwright not installed. Install with: pip install playwright && playwright install chromium")

if __name__ == "__main__":
    # Run the FastMCP server
    mcp.run(host="0.0.0.0", port=MCP_PORT)
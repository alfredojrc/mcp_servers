# 07_web_browsing_mcp (Port 8007)

## Purpose
Provides tools for web browsing, page interaction, and content extraction, likely using a headless browser like Playwright or Selenium.

Tools are organized under the `web.browse.*` namespace.

## Namespaced Tools (Examples)

- **`web.browse.navigation.*`**:
  - `navigateTo(url: str)`: Navigates the browser to a specific URL.
  - `getCurrentUrl() -> str`: Returns the current URL.
  - `goBack()`: Navigates back.
  - `goForward()`: Navigates forward.
- **`web.browse.interaction.*`**:
  - `clickElement(selector: str)`: Clicks an element matching the CSS selector (requires approval).
  - `fillForm(selector: str, value: str)`: Fills a form field (requires approval, mask sensitive values in logs).
  - `scrollPage(direction: str, amount: int)`: Scrolls the page.
- **`web.browse.extraction.*`**:
  - `getPageContent(format: str = 'markdown') -> str`: Extracts the full page content (e.g., as text or simplified Markdown).
  - `getElementText(selector: str) -> str`: Gets the text content of a specific element.
  - `getScreenshot(path: str | None = None) -> str | bytes`: Takes a screenshot (returns path if saved, or bytes).

## Container Layout
```
07_web_browsing_mcp/
├── Dockerfile
├── entrypoint.sh
├── requirements.txt     # Python MCP SDK, playwright/selenium
├── mcp_server.py
└── README.md
```

## Implementation Details
- **Framework:** Python with `mcp`/`fastmcp`.
- **Backend:** Uses Playwright (recommended for modern features) or Selenium to control a headless browser instance (e.g., Chromium) running within the same container or a linked container (like `seleniarm/standalone-chromium`).

## Operating Principles & Security Considerations
Interacts with the public web and potentially internal sites.

1.  **OS Discovery:** N/A.
2.  **Backup:** N/A.
3.  **Approval for Modifications:** Required for actions that interact with websites (`clickElement`, `fillForm`). Navigating is generally read-only but could trigger actions on some sites.
4.  **Read-Only Allowed:** Getting URL, extracting content/text, taking screenshots.
5.  **Logging:** Log URLs visited, selectors used, high-level actions taken (mask sensitive form values) using structured logging.
6.  **Shell Consistency:** N/A.
7.  **Sensitive File Access:** N/A (unless saving screenshots/downloads - ensure paths are restricted).
8.  **Interactive Commands:** N/A.
9.  **Critical Actions:** Filling forms on sensitive sites could be considered critical.

**Additional Security:**
- **Input Sanitization:** Sanitize URLs and selectors passed to tools.
- **Network Isolation:** Consider running the browser in a network sandbox if feasible.
- **Credential Handling:** Avoid hardcoding credentials for site logins; if login is needed, design tools carefully and potentially require credentials passed per-call (masked in logs).

## Configuration
- `MCP_PORT=8007`
- `BROWSER_TYPE` (e.g., `chromium`, `firefox`)
- `SELENIUM_GRID_URL` (If using a separate Selenium container)

## Observability
- **Logging:** Adheres to project JSON standard, includes `correlation_id`.
- **Metrics:** Implement `web.browse.getMetrics()` (e.g., pages loaded, actions performed).

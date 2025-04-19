# 06_web_search_mcp (Port 8006)

## Purpose
Provides tools for performing web searches using various search engines or APIs.

Tools are organized under the `web.search.*` namespace.

## Namespaced Tools (Examples)

- **`web.search.query(queryString: str, engine: str = 'google', numResults: int = 5) -> list[dict]`**: 
  Performs a web search using the specified engine (e.g., 'google', 'duckduckgo', 'bing', 'exa') and returns a list of results, typically including `title`, `link`, and `snippet`.

## Container Layout
```
06_web_search_mcp/
├── Dockerfile
├── entrypoint.sh
├── requirements.txt     # Python MCP SDK, requests, beautifulsoup4, specific API clients (e.g., google-api-python-client, duckduckgo_search, exa-py)
├── mcp_server.py
└── README.md
```

## Implementation Details
- **Framework:** Python with `mcp`/`fastmcp`.
- **Backend:** Can use official APIs (Google Custom Search JSON API, Bing Web Search API, Exa API) or libraries that scrape results (like `duckduckgo_search`, though scraping can be brittle).

## Operating Principles & Security Considerations
Primarily read-only interaction with external search APIs.

1.  **OS Discovery:** N/A.
2.  **Backup:** N/A.
3.  **Approval for Modifications:** N/A (this service is read-only).
4.  **Read-Only Allowed:** All search operations are read-only.
5.  **Logging:** Log search queries performed and the number of results returned using structured logging.
6.  **Shell Consistency:** N/A.
7.  **Sensitive File Access:** N/A.
8.  **Interactive Commands:** N/A.
9.  **Critical Actions:** N/A.

**Additional Security:**
- **API Key Security:** Store API keys for search engines securely using Docker secrets.
- **Rate Limiting:** Be mindful of API rate limits; implement client-side throttling if necessary.

## Configuration
- `MCP_PORT=8006`
- `GOOGLE_API_KEY_SECRET_PATH`
- `GOOGLE_CSE_ID`
- `BING_API_KEY_SECRET_PATH`
- `EXA_API_KEY_SECRET_PATH`

## Observability
- **Logging:** Adheres to project JSON standard, includes `correlation_id`.
- **Metrics:** Implement `web.search.getMetrics()` (e.g., searches performed by engine, API errors).

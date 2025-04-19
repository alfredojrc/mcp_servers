# 11_freqtrade_mcp (Port 8011)

## Purpose
Provides tools for interacting with a Freqtrade trading bot instance via its API.

Tools are organized under the `trading.freqtrade.*` namespace.

## Namespaced Tools (Examples)

- **`trading.freqtrade.status.*`**:
  - `getStatus() -> dict`: Gets the bot's current status.
  - `getPerformance() -> list[dict]`: Retrieves performance statistics.
  - `getBalance() -> dict`: Gets account balances.
  - `getOpenTrades() -> list[dict]`: Lists currently open trades.
- **`trading.freqtrade.control.*`**:
  - `startBot()`: Starts the bot (requires approval).
  - `stopBot()`: Stops the bot (requires approval).
  - `reloadConfig()`: Reloads the bot configuration (requires approval).
  - `forceEnter(pair: str, side: str, amount: float | None = None)`: Forces entry into a trade (requires approval).
  - `forceExit(tradeId: int | str)`: Forces exit from a trade (requires approval).

## Container Layout
```
11_freqtrade_mcp/
├── Dockerfile
├── entrypoint.sh
├── requirements.txt     # Python MCP SDK, requests
├── mcp_server.py        # Server implementation
└── README.md            # (this file)
```

## Implementation Details
- **Framework:** Python with `mcp`/`fastmcp` and the `requests` library to call the Freqtrade REST API.
- **Authentication:** Uses API credentials (username/password or token) configured for the Freqtrade API.

## Operating Principles & Security Considerations
Interacts with a live trading system.

1.  **OS Discovery:** N/A.
2.  **Backup Configurations:** Freqtrade configs should be version controlled.
3.  **Approval for Modifications:** Any action that starts/stops the bot, modifies trades (`forceEnter`/`forceExit`), or potentially reloads configuration requires explicit approval.
4.  **Read-Only Allowed:** Getting status, performance, balance, or listing trades is permitted without prior approval.
5.  **Logging:** Log all API calls made to Freqtrade, parameters (masking sensitive data), and responses/errors using structured logging.
6.  **Shell Consistency:** N/A.
7.  **Sensitive File Access:** N/A.
8.  **Interactive Commands:** N/A.
9.  **Critical Actions:** Starting/stopping the bot and forcing trades are critical actions requiring approval.

**Additional Security:**
- **API Credential Security:** Store Freqtrade API username/password securely using Docker secrets.
- **Network Security:** Ensure the Freqtrade API endpoint is appropriately secured (e.g., HTTPS, firewall rules).

## Configuration
- `MCP_PORT=8011`
- `FREQTRADE_API_URL` (URL of the Freqtrade API endpoint)
- `FREQTRADE_API_USER`
- `FREQTRADE_API_PASSWORD_SECRET_PATH` (Path to mounted Docker secret)

## Observability
- **Logging:** Adheres to project's JSON logging standard, including `correlation_id`.
- **Metrics:** Should implement `trading.freqtrade.getMetrics()`.

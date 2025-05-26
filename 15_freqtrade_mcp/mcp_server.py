import os
import logging
import json
from datetime import datetime as dt
import subprocess
import shlex
from typing import Optional, List, Dict, Any
import httpx

from mcp.server.fastmcp import FastMCP
from starlette.routing import Route
from starlette.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

load_dotenv()

# --- JSON Formatter Class (Standard) ---
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
        if record.stack_info:
            log_entry['stack_info'] = self.formatStack(record.stack_info)
        return json.dumps(log_entry)

# --- Logging Setup (Standard) ---
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

SERVICE_NAME = "freqtrade-mcp"
json_formatter = JSONFormatter(SERVICE_NAME)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(json_formatter)
root_logger.addHandler(stream_handler)
root_logger.setLevel(logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
MCP_PORT = int(os.getenv("MCP_PORT", "8015"))
FREQTRADE_USER_DATA_PATH = os.getenv("FREQTRADE_USER_DATA_PATH", "/app/user_data")
FREQTRADE_CONFIG_FILE = os.getenv("FREQTRADE_CONFIG_FILE", os.path.join(FREQTRADE_USER_DATA_PATH, "config.json"))

# Freqtrade API Configuration
FREQTRADE_API_URL = os.getenv("FREQTRADE_API_URL", "http://localhost:8080")
FREQTRADE_API_USER = os.getenv("FREQTRADE_API_USER")
FREQTRADE_API_PASS = os.getenv("FREQTRADE_API_PASS")
# Ensure API URL ends with /api/v1 if not already present
if not FREQTRADE_API_URL.endswith('/api/v1'):
    if FREQTRADE_API_URL.endswith('/'):
        FREQTRADE_API_URL += 'api/v1'
    else:
        FREQTRADE_API_URL += '/api/v1'

mcp_server = FastMCP(name=SERVICE_NAME, port=MCP_PORT)
http_client: Optional[httpx.AsyncClient] = None

async def get_http_client() -> httpx.AsyncClient:
    global http_client
    if http_client is None:
        auth = None
        if FREQTRADE_API_USER and FREQTRADE_API_PASS:
            auth = httpx.BasicAuth(FREQTRADE_API_USER, FREQTRADE_API_PASS)
        http_client = httpx.AsyncClient(base_url=FREQTRADE_API_URL, auth=auth, timeout=30.0)
    return http_client

# --- Health Check Endpoint (Standard) ---
async def health_check(request):
    # Check Freqtrade API health as part of this MCP's health
    client = await get_http_client()
    ft_healthy = False
    try:
        # Use /ping as it requires no auth if API server is up
        ping_url = FREQTRADE_API_URL.replace('/api/v1', '')
        if not ping_url.endswith('/'):
            ping_url += '/'
        ping_url += 'ping'
        
        # Temporary client for ping if main one uses auth
        async with httpx.AsyncClient(timeout=5.0) as temp_client:
            response = await temp_client.get(ping_url)
        if response.status_code == 200 and response.json().get("status") == "pong":
            ft_healthy = True
            ft_status_detail = "connected"
        else:
            ft_status_detail = f"ping failed with status {response.status_code}"
    except httpx.RequestError as e:
        ft_status_detail = f"request error: {str(e)}"
    except Exception as e:
        ft_status_detail = f"unexpected error: {str(e)}"

    return JSONResponse({
        "status": "healthy" if ft_healthy else "degraded",
        "service": SERVICE_NAME,
        "timestamp": dt.now().isoformat(),
        "dependencies": {
            "freqtrade_api": {
                "status": "healthy" if ft_healthy else "unhealthy",
                "detail": ft_status_detail,
                "url": FREQTRADE_API_URL.replace('/api/v1', '')
            }
        }
    })

# --- Helper to call Freqtrade REST API ---
async def call_freqtrade_api(method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    client = await get_http_client()
    try:
        logger.info(f"Calling Freqtrade API: {method} {endpoint} with params={params}, json_data={json_data}")
        response = await client.request(method, endpoint, params=params, json=json_data)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Freqtrade API HTTP error: {e.response.status_code} - {e.response.text}", exc_info=True)
        return {"error": "API request failed", "status_code": e.response.status_code, "details": e.response.text}
    except httpx.RequestError as e:
        logger.error(f"Freqtrade API request error: {e}", exc_info=True)
        return {"error": "API request failed", "details": str(e)}
    except json.JSONDecodeError:
        logger.error(f"Freqtrade API JSON decode error for response: {response.text}", exc_info=True)
        return {"error": "Invalid JSON response from API", "details": response.text}
    except Exception as e:
        logger.error(f"Unexpected error calling Freqtrade API: {e}", exc_info=True)
        return {"error": "Unexpected error", "details": str(e)}

# --- Helper to run Freqtrade CLI commands (for actions not easily done via API) ---
def run_freqtrade_command(command_args: List[str], user_data_path: Optional[str] = None, config_file: Optional[str] = None) -> Dict[str, Any]:
    """Runs a Freqtrade CLI command and returns its output."""
    base_command = ["freqtrade"]
    
    # Prepend user_data_path and config if specified and not already in command_args
    if user_data_path and "--userdir" not in command_args and "--user-dir" not in command_args:
        base_command.extend(["--userdir", user_data_path])
    
    if config_file and "--config" not in command_args and "-c" not in command_args:
        base_command.extend(["--config", config_file])
    
    full_command = base_command + command_args
    
    logger.info(f"Executing Freqtrade command: {' '.join(shlex.quote(arg) for arg in full_command)}")
    try:
        process = subprocess.run(full_command, capture_output=True, text=True, check=False, timeout=300) # 5 min timeout
        return {
            "stdout": process.stdout,
            "stderr": process.stderr,
            "exit_code": process.returncode,
            "command_executed": ' '.join(full_command) # For debugging
        }
    except subprocess.TimeoutExpired:
        logger.error(f"Freqtrade command timed out: {' '.join(full_command)}")
        return {"error": "Command timed out", "stdout": "", "stderr": "Timeout after 300 seconds."}
    except Exception as e:
        logger.error(f"Error executing Freqtrade command {' '.join(full_command)}: {e}", exc_info=True)
        return {"error": str(e), "stdout": "", "stderr": str(e)}

# --- MCP Tool Definitions ---

@mcp_server.tool("freqtrade.listStrategies")
async def list_strategies() -> Dict[str, Any]:
    """Lists available strategies by calling the Freqtrade REST API."""
    # The Freqtrade CLI 'list-strategies' is simple, but API provides structured output.
    # API endpoint: /api/v1/strategies
    # Note: This API returns the *content* of the strategy files if they exist in default path,
    # or a list of strategy names if they are not in the default path or other issues.
    # We are interested in the list of names.
    
    # The CLI command `freqtrade list-strategies --userdir /app/user_data` is more reliable for just names.
    # However, let's try the API first as per the goal to shift to API.
    # If the API returns a list of objects with "name" and "location", that's good.
    # If it returns raw file content, we might fall back or parse differently.

    api_response = await call_freqtrade_api("GET", "/strategies")
    if "error" in api_response:
        logger.warning("Failed to list strategies via API, falling back to CLI.")
        # Fallback to CLI if API fails or doesn't provide a simple list
        return run_freqtrade_command(["list-strategies"], user_data_path=FREQTRADE_USER_DATA_PATH)

    # The API returns a list of dictionaries, each with 'name' and 'location'
    # e.g., [{"name": "Strategy001", "location": "/freqtrade/user_data/strategies/Strategy001.py"}, ...]
    # Or, if it directly returns strategy code, it means something else.
    # The current documentation suggests it "List strategies in strategy directory."
    # And the example client output shows it lists them.
    
    # Assuming the API returns a list of strategy dicts (name, location) or just a list of names
    if isinstance(api_response, list):
        strategy_names = []
        for item in api_response:
            if isinstance(item, dict) and "name" in item:
                strategy_names.append(item["name"])
            elif isinstance(item, str): # Fallback if it's just a list of strings
                strategy_names.append(item)
        if strategy_names:
             return {"strategies": strategy_names, "source": "API"}
        else: # If API returned empty or unexpected list structure
            logger.warning("API for list_strategies returned unexpected structure, falling back to CLI.")
            return run_freqtrade_command(["list-strategies"], user_data_path=FREQTRADE_USER_DATA_PATH)

    # If the response is not a list, it's unexpected. Fallback.
    logger.warning(f"API for list_strategies returned unexpected type {type(api_response)}, falling back to CLI.")
    return run_freqtrade_command(["list-strategies"], user_data_path=FREQTRADE_USER_DATA_PATH)

@mcp_server.tool("freqtrade.downloadData")
async def download_data(pairs: List[str], days: Optional[int] = None, timeframe: Optional[str] = None, exchange: Optional[str] = None) -> Dict[str, Any]:
    """Downloads historical data for the given pairs using Freqtrade CLI."""
    # No direct API endpoint to trigger data download; this is a CLI-centric operation.
    command = ["download-data", "--pairs"] + pairs
    if days:
        command.extend(["--days", str(days)])
    if timeframe:
        command.extend(["--timeframe", timeframe])
    if exchange:
        command.extend(["--exchange", exchange])
    # Note: run_freqtrade_command is synchronous, consider running in a threadpool if it blocks too long.
    # For now, MCP server tools can be async and await sync functions if needed,
    # but true async subprocess execution would be better for long-running commands.
    # However, FastMCP tools are typically expected to be relatively quick or handle long tasks internally.
    # Let's assume download-data is acceptable as a blocking call for now.
    return run_freqtrade_command(command, user_data_path=FREQTRADE_USER_DATA_PATH, config_file=FREQTRADE_CONFIG_FILE)

@mcp_server.tool("freqtrade.backtest")
async def backtest(strategy: str, timerange: Optional[str] = None, exchange: Optional[str] = None) -> Dict[str, Any]:
    """Runs a backtest for a given strategy using Freqtrade CLI."""
    # No direct API endpoint to trigger a full backtest and get results; CLI-centric.
    command = ["backtesting", "--strategy", strategy]
    if timerange:
        command.extend(["--timerange", timerange])
    if exchange:
        command.extend(["--exchange", exchange])
    return run_freqtrade_command(command, user_data_path=FREQTRADE_USER_DATA_PATH, config_file=FREQTRADE_CONFIG_FILE)

# --- Freqtrade API Based Tools ---

@mcp_server.tool("freqtrade.api.getStatus")
async def get_status() -> Dict[str, Any]:
    """Gets the status of all open trades from the Freqtrade API (/status)."""
    return await call_freqtrade_api("GET", "/status")

@mcp_server.tool("freqtrade.api.getTradeCount")
async def get_trade_count() -> Dict[str, Any]:
    """Gets the count of open trades and available trade slots from Freqtrade API (/count)."""
    return await call_freqtrade_api("GET", "/count")

@mcp_server.tool("freqtrade.api.startBot")
async def start_bot() -> Dict[str, Any]:
    """Starts the Freqtrade bot via API (/start). Assumes bot is in a stopped state."""
    return await call_freqtrade_api("POST", "/start")

@mcp_server.tool("freqtrade.api.stopBot")
async def stop_bot() -> Dict[str, Any]:
    """Stops the Freqtrade bot via API (/stop). Bot can be restarted with startBot."""
    return await call_freqtrade_api("POST", "/stop")

@mcp_server.tool("freqtrade.api.pauseBot")
async def pause_bot() -> Dict[str, Any]:
    """Pauses the Freqtrade bot via API (/pause). Handles open trades, no new positions. Use startBot to resume fully."""
    return await call_freqtrade_api("POST", "/pause")

@mcp_server.tool("freqtrade.api.stopBuy")
async def stop_buy() -> Dict[str, Any]:
    """Stops the Freqtrade bot from opening new buy trades via API (/stopbuy). Existing sell orders are handled. Use reloadConfig to reset."""
    return await call_freqtrade_api("POST", "/stopbuy")

@mcp_server.tool("freqtrade.api.reloadConfig")
async def reload_config() -> Dict[str, Any]:
    """Reloads the Freqtrade bot's configuration from disk via API (/reload_config)."""
    return await call_freqtrade_api("POST", "/reload_config")

@mcp_server.tool("freqtrade.api.getBotHealth")
async def get_bot_health() -> Dict[str, Any]:
    """Gets Freqtrade's internal health check status (/health). Differs from MCP /health."""
    return await call_freqtrade_api("GET", "/health")

@mcp_server.tool("freqtrade.api.getVersion")
async def get_version() -> Dict[str, Any]:
    """Gets the running Freqtrade instance version from API (/version)."""
    return await call_freqtrade_api("GET", "/version")

@mcp_server.tool("freqtrade.api.showConfig")
async def show_config() -> Dict[str, Any]:
    """Shows relevant parts of the current operational Freqtrade configuration via API (/show_config)."""
    return await call_freqtrade_api("GET", "/show_config")

@mcp_server.tool("freqtrade.api.getBalance")
async def get_balance() -> Dict[str, Any]:
    """Gets account balance per currency from Freqtrade API (/balance)."""
    return await call_freqtrade_api("GET", "/balance")

@mcp_server.tool("freqtrade.api.getProfitSummary")
async def get_profit_summary() -> Dict[str, Any]:
    """Gets a summary of profit/loss from closed trades via Freqtrade API (/profit)."""
    return await call_freqtrade_api("GET", "/profit")

@mcp_server.tool("freqtrade.api.getDailyStats")
async def get_daily_stats(days: Optional[int] = 7) -> Dict[str, Any]:
    """Gets profit or loss per day for the last N days from Freqtrade API (/daily). Default N=7."""
    params = None
    if days is not None:
        params = {"days": days} # Freqtrade API expects 'days' as param key based on help text, not 'n'
    return await call_freqtrade_api("GET", "/daily", params=params)

@mcp_server.tool("freqtrade.api.getPerformance")
async def get_performance() -> Dict[str, Any]:
    """Gets performance of each finished trade, grouped by pair, from Freqtrade API (/performance)."""
    return await call_freqtrade_api("GET", "/performance")

@mcp_server.tool("freqtrade.api.getTradesHistory")
async def get_trades_history(limit: Optional[int] = None, offset: Optional[int] = None) -> Dict[str, Any]:
    """Gets history of closed trades from Freqtrade API (/trades). Limit and offset are optional."""
    params: Dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    return await call_freqtrade_api("GET", "/trades", params=params if params else None)

@mcp_server.tool("freqtrade.api.getTrade")
async def get_trade(trade_id: int) -> Dict[str, Any]:
    """Gets details for a specific trade by its ID from Freqtrade API (/trade/{trade_id})."""
    return await call_freqtrade_api("GET", f"/trade/{trade_id}")

@mcp_server.tool("freqtrade.api.getWhitelist")
async def get_whitelist() -> Dict[str, Any]:
    """Gets the current whitelist from Freqtrade API (/whitelist)."""
    return await call_freqtrade_api("GET", "/whitelist")

@mcp_server.tool("freqtrade.api.getBlacklist")
async def get_blacklist() -> Dict[str, Any]:
    """Gets the current blacklist from Freqtrade API (/blacklist)."""
    return await call_freqtrade_api("GET", "/blacklist")

@mcp_server.tool("freqtrade.api.addToBlacklist")
async def add_to_blacklist(pair: str) -> Dict[str, Any]:
    """Adds a trading pair to the blacklist via Freqtrade API (/blacklist POST)."""
    # The API expects {'pair': 'PAIR_TO_BLACKLIST'} in the JSON body
    return await call_freqtrade_api("POST", "/blacklist", json_data={"pair": pair})

@mcp_server.tool("freqtrade.api.deleteFromBlacklist")
async def delete_from_blacklist(pairs: List[str]) -> Dict[str, Any]:
    """Removes one or more trading pairs from the blacklist via Freqtrade API (/blacklist DELETE)."""
    # The API expects a list of pairs in the JSON body {'pairs': ['PAIR1', 'PAIR2']}
    # or as a query parameter like ?pair=PAIR1&pair=PAIR2
    # For simplicity and consistency with POST, using JSON body.
    return await call_freqtrade_api("DELETE", "/blacklist", json_data={"pairs": pairs})

@mcp_server.tool("freqtrade.api.getLocks")
async def get_locks() -> Dict[str, Any]:
    """Gets all active pair locks from Freqtrade API (/locks)."""
    return await call_freqtrade_api("GET", "/locks")

@mcp_server.tool("freqtrade.api.addLock")
async def add_lock(pair: str, until: str, side: Optional[str] = None, reason: Optional[str] = None) -> Dict[str, Any]:
    """Locks a trading pair until a specified datetime via Freqtrade API (/locks POST).
    `until` should be a datetime string e.g., '2024-12-31 23:59:59'. 
    `side` can be 'long', 'short', or '*'.
    """
    json_payload: Dict[str, Any] = {"pair": pair, "until": until}
    if side:
        json_payload["side"] = side
    if reason:
        json_payload["reason"] = reason
    return await call_freqtrade_api("POST", "/locks", json_data=json_payload)

@mcp_server.tool("freqtrade.api.deleteLock")
async def delete_lock(lock_id: int) -> Dict[str, Any]:
    """Deletes a specific pair lock by its ID via Freqtrade API (/locks/{lock_id} DELETE)."""
    return await call_freqtrade_api("DELETE", f"/locks/{lock_id}")

@mcp_server.tool("freqtrade.api.forceEnter")
async def force_enter(
    pair: str, 
    side: Optional[str] = "long", 
    rate: Optional[float] = None,
    stake_amount: Optional[float] = None, # Added stake_amount based on common need, though API doc doesn't explicitly list it for /forceenter, /forcebuy implies it
    enter_tag: Optional[str] = None # Added for tracking forced entries
) -> Dict[str, Any]:
    """Forces an entry for a pair via Freqtrade API (/forceenter POST).
    Requires `force_entry_enable: true` in Freqtrade config.
    `side` defaults to 'long'. `rate` is optional entry price.
    `stake_amount` is optional. `enter_tag` is an optional tag for the trade.
    """
    json_payload: Dict[str, Any] = {"pair": pair}
    if side:
        json_payload["side"] = side
    if rate is not None: # Check for None as rate could be 0.0
        json_payload["price"] = rate # API docs for /forceenter list 'price' not 'rate'
    if stake_amount is not None:
        json_payload["stake_amount"] = stake_amount
    if enter_tag is not None:
        json_payload["enter_tag"] = enter_tag
        
    # The /forcebuy endpoint (which /forceenter seems to be a more generic version of)
    # also takes `leverage`, `stop_loss_price`, `take_profit_price`.
    # For now, sticking to documented /forceenter params + common additions.
    return await call_freqtrade_api("POST", "/forceenter", json_data=json_payload)

@mcp_server.tool("freqtrade.api.forceExit")
async def force_exit(trade_id: str, order_type: Optional[str] = None, amount: Optional[float] = None, exit_reason: Optional[str] = None) -> Dict[str, Any]:
    """Forces an exit for a trade via Freqtrade API (/forceexit POST).
    `trade_id` can be a specific ID or 'all' to exit all open trades.
    `order_type` can be 'market' or 'limit'. Uses config default if None.
    `amount` is optional partial exit amount. `exit_reason` is an optional tag.
    """
    json_payload: Dict[str, Any] = {"tradeid": trade_id} # API uses 'tradeid'
    if order_type:
        json_payload["ordertype"] = order_type
    if amount is not None:
        json_payload["amount"] = amount
    if exit_reason is not None:
        json_payload["exit_reason"] = exit_reason
    return await call_freqtrade_api("POST", "/forceexit", json_data=json_payload)

# --- CLI Based tools for Hyperopt & FreqAI (to be developed further) ---

@mcp_server.tool("freqtrade.cli.runHyperopt")
async def run_hyperopt(
    strategy: str,
    epochs: int = 100,
    spaces: Optional[List[str]] = None, # e.g. ["buy", "sell", "roi"]
    hyperopt_loss: Optional[str] = None, # e.g., SharpeHyperOptLossDaily
    timerange: Optional[str] = None, # e.g., 20230101-
    min_trades: Optional[int] = 1,
    job_workers: Optional[int] = -1, # -1 for all cores
    random_state: Optional[int] = None,
    extra_args: Optional[List[str]] = None # For any other hyperopt flags
) -> Dict[str, Any]:
    """Runs Freqtrade hyperopt for a given strategy using Freqtrade CLI."""
    command = ["hyperopt", "--strategy", strategy, "--epochs", str(epochs)]
    
    if spaces:
        command.extend(["--spaces"] + spaces)
    if hyperopt_loss:
        command.extend(["--hyperopt-loss", hyperopt_loss])
    if timerange:
        command.extend(["--timerange", timerange])
    if min_trades is not None:
        command.extend(["--min-trades", str(min_trades)])
    if job_workers is not None:
        command.extend(["--job-workers", str(job_workers)])
    if random_state is not None:
        command.extend(["--random-state", str(random_state)])
    if extra_args:
        command.extend(extra_args)
        
    return run_freqtrade_command(command, user_data_path=FREQTRADE_USER_DATA_PATH, config_file=FREQTRADE_CONFIG_FILE)

@mcp_server.tool("freqtrade.cli.freqaiTrain")
async def freqai_train(
    strategy: str, 
    timerange: Optional[str] = None,
    extra_args: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Triggers FreqAI model training for a given strategy using Freqtrade CLI."""
    command = ["freqai-train", "--strategy", strategy] # Actual command might differ, e.g. integrated into `trade` with specific flags
    # TODO: Verify actual FreqAI training command and its parameters from Freqtrade docs/CLI help.
    # This is a placeholder structure.
    # Example: `freqtrade trade --config config-freqai.json --strategy MyFreqAIStrat --freqaimodel MyModel --train-freqaimodel` (this is a guess)
    # For now, assuming a direct `freqai-train` or similar subcommand might exist or be planned.
    # Or it's part of `trade` with specific FreqAI flags.
    
    # The Freqtrade docs suggest running trade with FreqAI config and strategy:
    # `freqtrade trade --config config_examples/config_freqai.example.json --strategy FreqaiExampleStrategy`
    # Training is often part of the initial run or controlled by config.
    # A dedicated CLI for *just* training might not be the primary way, but a tool to trigger it is useful.
    
    # Let's assume for now we will use the `trade` command with specific flags if a separate `freqai-train` does not exist.
    # This tool would then construct that more complex `trade` command.
    # For now, keeping it simple as `freqai-train` placeholder.
    
    if timerange:
        command.extend(["--timerange", timerange])
    if extra_args:
        command.extend(extra_args)
        
    # This tool will likely need refinement based on how FreqAI training is best triggered via CLI for automation.
    logger.warning("freqtrade.cli.freqaiTrain is a placeholder and may need command adjustments based on Freqtrade CLI for FreqAI.")
    return run_freqtrade_command(command, user_data_path=FREQTRADE_USER_DATA_PATH, config_file=FREQTRADE_CONFIG_FILE)

# --- Knowledge Base Tools (Populated) ---
@mcp_server.tool("freqtrade.knowledge.hyperoptBestPractices")
async def hyperopt_best_practices() -> Dict[str, Any]:
    """Provides best practices for Freqtrade Hyperopt."""
    # Based on Freqtrade documentation (https://www.freqtrade.io/en/stable/hyperopt/)
    # and general ML hyperparameter tuning principles.
    return {
        "title": "Freqtrade Hyperopt Best Practices",
        "summary": "Key recommendations for effective hyperparameter optimization in Freqtrade.",
        "practices": [
            {
                "point": "Understand Hyperopt Basics",
                "details": "Hyperopt uses scikit-optimize (Bayesian search) to find optimal strategy parameters. It runs backtests repeatedly with different parameters to minimize a loss function.",
                "keywords": ["bayesian search", "scikit-optimize", "loss function", "backtesting"]
            },
            {
                "point": "Install Dependencies",
                "details": "Ensure hyperopt dependencies are installed: `pip install -r requirements-hyperopt.txt`. Docker images usually include them.",
                "keywords": ["dependencies", "requirements-hyperopt.txt"]
            },
            {
                "point": "Data is Key",
                "details": "Hyperopt requires sufficient, good quality historical data. Download data using `freqtrade download-data`.",
                "keywords": ["historical data", "download-data"]
            },
            {
                "point": "Define Hyperoptable Parameters in Strategy",
                "details": "Use `IntParameter`, `DecimalParameter`, `CategoricalParameter`, `BooleanParameter` directly in your strategy class. Assign them to `buy_*` / `sell_*` names or use `space='buy'/'sell'/'protection'`.",
                "example": "`buy_rsi_value = IntParameter(10, 40, default=30, space='buy')`",
                "keywords": ["IntParameter", "DecimalParameter", "CategoricalParameter", "BooleanParameter", "parameter spaces"]
            },
            {
                "point": "Choose the Right Loss Function",
                "details": "Select a loss function (`--hyperopt-loss`) that aligns with your goals (e.g., `SharpeHyperOptLossDaily`, `SortinoHyperOptLossDaily`, `OnlyProfitHyperOptLoss`, `MaxDrawDownHyperOptLoss`). Custom loss functions can be created.",
                "keywords": ["loss function", "Sharpe", "Sortino", "profit", "drawdown"]
            },
            {
                "point": "Specify Search Spaces",
                "details": "Use the `--spaces` argument to target specific parameter groups (e.g., `buy`, `sell`, `roi`, `stoploss`, `trailing`, `protection`). Optimizing everything at once (`--spaces all`) can be very slow and less effective.",
                "tip": "Optimize spaces iteratively: e.g., first 'buy', then 'sell', then 'roi' and 'stoploss'.",
                "keywords": ["search space", "iterative optimization"]
            },
            {
                "point": "Control Number of Epochs",
                "details": "Use `-e` or `--epochs` to set the number of evaluations. Too few epochs might not find good optima; too many might overfit or yield diminishing returns. 500-1000 epochs is often a good starting range, then analyze.",
                "keywords": ["epochs", "evaluations", "overfitting"]
            },
            {
                "point": "Use Timerange Selectively",
                "details": "Use `--timerange` to optimize on specific periods. Optimizing on recent data might be more relevant for current market conditions, but ensure enough data for statistical significance.",
                "keywords": ["timerange", "market conditions"]
            },
            {
                "point": "Parallel Processing (Jobs)",
                "details": "Use `-j` or `--job-workers` to specify concurrent processes. `-1` uses all CPUs. Be mindful of RAM usage per job.",
                "keywords": ["job-workers", "parallelism", "CPU", "RAM"]
            },
            {
                "point": "Reproducibility",
                "details": "Use `--random-state <integer>` for reproducible hyperopt runs, as the initial search involves randomness.",
                "keywords": ["random-state", "reproducibility"]
            },
            {
                "point": "Analyze Results",
                "details": "Hyperopt saves results in `user_data/hyperopt_results/`. Use `freqtrade hyperopt-list` and `freqtrade hyperopt-show` to inspect. The best parameters are also saved to a `.json` file next to your strategy.",
                "keywords": ["results analysis", "hyperopt-list", "hyperopt-show"]
            },
            {
                "point": "Validate Optimized Parameters",
                "details": "Always backtest your strategy with the hyperopt-derived parameters to confirm performance. Hyperopt results are for a specific dataset and loss function; real-world performance may vary.",
                "keywords": ["validation", "backtesting confirmation"]
            },
            {
                "point": "Avoid Overfitting",
                "details": "Be cautious of overfitting to the specific historical data used. Test on out-of-sample data if possible. Simpler strategies with fewer parameters are often more robust.",
                "keywords": ["overfitting", "out-of-sample testing", "robustness"]
            },
            {
                "point": "Optimize Indicator Parameters Carefully",
                "details": "When optimizing indicator parameters (e.g., EMA periods), ensure indicators are recalculated for each epoch. This can be done by defining them in `populate_entry_trend`/`populate_exit_trend` or using `--analyze-per-epoch` if they are in `populate_indicators` and use the `.range` attribute.",
                "warning": "Using `.range` in `populate_indicators` without `--analyze-per-epoch` pre-calculates all variants, consuming significant RAM.",
                "keywords": ["indicator parameters", "analyze-per-epoch", "RAM usage"]
            },
             {
                "point": "Iterative Refinement",
                "details": "Hyperopt is often an iterative process. Start with broader ranges and fewer epochs, then narrow down ranges and increase epochs for promising parameter sets.",
                "keywords": ["iterative refinement", "focused search"]
            }
        ],
        "common_issues": [
            {"issue": "Out of Memory errors", "solution": "Reduce pairs, timerange, job workers, or use --analyze-per-epoch if optimizing many indicator params with .range."},
            {"issue": "'The objective has been evaluated at this point before.' warning", "solution": "Search space might be too small or exhausted. Consider expanding ranges or reducing epochs for that specific space."},
            {"issue": "Backtest results don't match hyperopt results", "solution": "Ensure same config (timerange, fee, stake, etc.), protections are handled consistently, and parameters are correctly applied without overrides from config."}
        ],
        "cli_example": "`freqtrade hyperopt -s YourStrategy --epochs 500 --spaces buy stoploss --hyperopt-loss SharpeHyperOptLossDaily --timerange 20230101-`"
    }

@mcp_server.tool("freqtrade.knowledge.freqAiOverview")
async def freqai_overview(version_focus: Optional[str] = "modern") -> Dict[str, Any]:
    """Explains FreqAI, focusing on modern vs. legacy versions if applicable (though FreqAI is largely a unified concept now)."""
    # Based on Freqtrade documentation (https://www.freqtrade.io/en/stable/freqai/)
    
    # Note: The concept of a distinct "legacy" vs "modern" FreqAI isn't strongly emphasized in current docs.
    # FreqAI has evolved. The main distinction might be older versions/approaches vs. current capabilities.
    # The tool will primarily describe current FreqAI.

    overview = {
        "title": "FreqAI Overview",
        "summary": "FreqAI is Freqtrade's module for integrating machine learning models into trading strategies. It automates training, feature engineering, and prediction for market forecasting.",
        "key_features": [
            {
                "feature": "Self-Adaptive Retraining",
                "description": "Models can be retrained during live deployments to adapt to changing market conditions.",
                "keywords": ["adaptive learning", "live retraining", "market adaptation"]
            },
            {
                "feature": "Rapid Feature Engineering",
                "description": "Allows creation of large, rich feature sets from strategy-defined base indicators.",
                "keywords": ["feature engineering", "custom indicators", "data transformation"]
            },
            {
                "feature": "High Performance",
                "description": "Uses threading for model retraining and inferencing, separate from bot operations. Supports GPU if available.",
                "keywords": ["performance", "threading", "GPU support"]
            },
            {
                "feature": "Realistic Backtesting",
                "description": "Emulates self-adaptive training on historical data, including periodic retraining.",
                "keywords": ["backtesting", "realistic simulation", "historical analysis"]
            },
            {
                "feature": "Extensibility",
                "description": "Supports various machine learning libraries (e.g., scikit-learn, LightGBM, CatBoost, PyTorch via specific Docker images). Users can integrate custom models.",
                "keywords": ["extensibility", "scikit-learn", "LightGBM", "CatBoost", "PyTorch", "custom models"]
            },
            {
                "feature": "Data Handling",
                "description": "Includes smart outlier removal, automatic data normalization, NaN handling, and dimensionality reduction (PCA).",
                "keywords": ["data preprocessing", "outlier detection", "normalization", "PCA"]
            },
            {
                "feature": "Crash Resilience & Deployment",
                "description": "Stores trained models to disk for fast reloading. Supports producer/consumer mode for bot fleets.",
                "keywords": ["model persistence", "crash recovery", "bot fleets"]
            }
        ],
        "general_approach": {
            "concept": "Users provide base indicators (features) and define target values (labels, e.g., future price movement). FreqAI trains a model per pair to predict labels from features, with periodic retraining.",
            "steps": [
                "Define base indicators in strategy (like a normal Freqtrade strategy).",
                "Define how to calculate labels (what the model should predict).",
                "Configure FreqAI settings in `config.json` (e.g., model type, retraining frequency, feature parameters).",
                "FreqAI handles data splitting (train/test), model training, prediction, and trade signal generation based on model output."
            ],
            "vocabulary": [
                {"term": "Features", "definition": "Input parameters for the model, derived from historical data and indicators."},
                {"term": "Labels", "definition": "Target values the model learns to predict (e.g., % price change in X future candles)."},
                {"term": "Training", "definition": "Process of teaching the model to map features to labels."},
                {"term": "Inferencing", "definition": "Using the trained model to make predictions on new, unseen data."}
            ]
        },
        "setup_and_usage": {
            "installation": "Install FreqAI dependencies (`pip install -r requirements-freqai.txt`). Docker images like `freqtradeorg/freqtrade:stable_freqai` or `stable_freqaitorch` include them.",
            "configuration_keys": [
                "`freqai` section in `config.json` is crucial.",
                "`enabled: true` to activate FreqAI.",
                "`freqaimodel`: Specifies the ML model to use (e.g., `LightGBMRegressor`, `ReinforcementLearner`, custom models).",
                "`feature_engineering_space`: Defines parameters for generating features (e.g., lags, diffs, technical indicators).",
                "`data_split_parameters`: Controls how data is split for training/testing.",
                "`model_training_parameters`: Parameters specific to the chosen ML model."
            ],
            "strategy_integration": [
                "Strategy class inherits from `IFreqaiStrategy` (which inherits `IStrategy`).",
                "`INTERFACE_VERSION = 3` (or higher, check docs).",
                "Implement `populate_any_indicators()` for base indicators, feature engineering (if not solely reliant on FreqAI config), and label creation.",
                "`set_freqai_targets()` is a key method where you define your prediction target(s) (labels).",
                "Entry/exit signals can then use `dataframe['&s-ML_BUY_SIGNAL']` or `dataframe['&s-ML_SELL_SIGNAL']` (or custom output names) generated by FreqAI."
            ],
            "cli_commands": [
                "`freqtrade trade --config config_freqai.json --strategy YourFreqAIStrategy` to run.",
                "Backtesting and hyperopt work similarly but require FreqAI-specific configurations."
            ]
        },
        "modern_vs_legacy_notes": {
            "focus": "Current FreqAI is a comprehensive framework. 'Legacy' might refer to earlier iterations with less integrated feature engineering, fewer model choices, and a more manual setup process. Key improvements in modern FreqAI include the `IFreqaiStrategy` interface, streamlined configuration, and robust backtesting of retraining cycles.",
            "evolution_points": [
                "More integrated feature engineering directly configurable in `config.json`.",
                "Improved data handling and preprocessing pipeline.",
                "Broader support for different ML model types and libraries.",
                "More robust backtesting that simulates retraining cycles.",
                "Clearer strategy interface (`IFreqaiStrategy`, `set_freqai_targets`). Version 2023.3 introduced `populate_any_indicators` replacing older indicator methods for FreqAI strategies, and `set_freqai_targets` for defining labels.",
                "Prior to `INTERFACE_VERSION = 2` (around Freqtrade 2021.10 and earlier), FreqAI was more experimental and less feature-rich. `IFreqaiStrategy` and its specific methods were introduced/formalized over time.",
                "The main change with newer versions (e.g. `INTERFACE_VERSION = 3`) is often refinement, more options, and better separation of concerns between strategy code and FreqAI's core logic for feature generation/model training based on config."
            ],
            "current_best_practice": "Follow the latest Freqtrade documentation for FreqAI setup and strategy implementation. Use the provided example strategies and configurations as starting points.",
            "version_focus_parameter_note": f"This overview focuses on current ('{version_focus}') FreqAI capabilities. Specific deprecated features or older behaviors are detailed in Freqtrade's release notes and migration guides.",
        },
        "common_pitfalls": [
            {"pitfall": "Data Requirements", "solution": "FreqAI needs substantial, clean historical data for training. Insufficient or poor-quality data leads to bad models."},
            {"pitfall": "Overfitting", "solution": "ML models can easily overfit to historical data. Use proper train/test/validation splits, regularization, and be skeptical of amazing backtest results."},
            {"pitfall": "Complexity", "solution": "FreqAI adds significant complexity. Start simple with features and models, then gradually increase complexity."},
            {"pitfall": "Pairlist Compatibility", "solution": "FreqAI generally works best with static or shuffle pairlists. Dynamic pairlists that add new pairs during a run can cause issues as FreqAI needs to download all data upfront."},
            {"pitfall": "Resource Intensive", "solution": "Training ML models can be CPU and RAM intensive. Ensure your system has adequate resources, especially for retraining during live runs."}
        ],
        "example_model_types": ["LightGBM (Regressor/Classifier)", "CatBoost", "Scikit-learn models (e.g., RandomForest, SVM)", "Reinforcement Learning models", "PyTorch-based Neural Networks (via specific Docker images)"],
        "citation": "FreqAI is a published software: Caulk et al., (2022). FreqAI: generalizing adaptive modeling for chaotic time-series market forecasts. Journal of Open Source Software, 7(80), 4864. https://doi.org/10.21105/joss.04864"
    }
    
    # If a very specific "legacy" version comparison is needed, more targeted historical doc searches would be required.
    # For now, this provides a good overview of current FreqAI.
    if version_focus == "legacy":
        overview["summary"] += " When comparing to 'legacy' FreqAI, this typically refers to earlier iterations with less integrated feature engineering, fewer model choices, and a more manual setup process. Key improvements in modern FreqAI include the `IFreqaiStrategy` interface, streamlined configuration, and robust backtesting of retraining cycles.\n        # Could add more specific points if known, e.g. differences in key config parameters or strategy methods."
        
    return overview

# --- Server Execution (Standard) ---
if __name__ == "__main__":
    async def app_startup():
        global http_client
        auth = None
        if FREQTRADE_API_USER and FREQTRADE_API_PASS:
            auth = httpx.BasicAuth(FREQTRADE_API_USER, FREQTRADE_API_PASS)
        http_client = httpx.AsyncClient(base_url=FREQTRADE_API_URL, auth=auth, timeout=30.0)
        logger.info("HTTPX Client for Freqtrade API initialized.")

    async def app_shutdown():
        if http_client:
            await http_client.aclose()
            logger.info("HTTPX Client for Freqtrade API closed.")

    app = mcp_server.sse_app(on_startup=[app_startup], on_shutdown=[app_shutdown])
    app.routes.append(Route("/health", health_check))
    
    logger.info(f"Starting {SERVICE_NAME} on port {MCP_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT, log_level="info") 
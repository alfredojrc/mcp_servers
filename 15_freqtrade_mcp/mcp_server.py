import os
import logging
import json
from datetime import datetime as dt
import subprocess
import shlex
from typing import Optional, List, Dict, Any, Tuple, Union
import httpx
import asyncio

from fastmcp import FastMCP
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
        if hasattr(record, 'props') and record.props:
            log_entry['props'] = record.props
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        if record.stack_info:
            log_entry['stack_info'] = self.formatStack(record.stack_info)
        return json.dumps(log_entry)

# --- Logging Setup (Standard) ---
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

SERVICE_NAME = "freqtrade-mcp-knowledge-hub"
json_formatter = JSONFormatter(SERVICE_NAME)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(json_formatter)
root_logger.addHandler(stream_handler)
root_logger.setLevel(logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
MCP_PORT = int(os.getenv("MCP_PORT", "8015"))
FREQTRADE_SRC_PATH = "/freqtrade" # Path where Freqtrade source is in the base image

# --- FastMCP Server Setup ---
mcp_server = FastMCP(name="freqtrade-knowledge-hub", port=MCP_PORT, host="0.0.0.0")

# --- Helper Functions ---

async def run_local_command(command_str: str, working_dir: Optional[str] = None) -> Tuple[int, str, str]:
    """
    Run a command locally within the container.
    Returns: (return_code, stdout, stderr)
    """
    try:
        cmd_list = shlex.split(command_str)
        proc = await asyncio.create_subprocess_exec(
            *cmd_list,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
        stdout = stdout_bytes.decode('utf-8', errors='replace') if stdout_bytes else ""
        stderr = stderr_bytes.decode('utf-8', errors='replace') if stderr_bytes else ""
        return proc.returncode or 0, stdout, stderr
    except Exception as e:
        logger.error(f"Failed to run command '{command_str}': {e}", exc_info=True)
        return -1, "", str(e)

# --- Knowledge Base Tools ---

@mcp_server.tool("freqtrade.knowledge.hyperoptBestPractices")
def freqtrade_hyperopt_best_practices() -> Dict[str, Any]:
    """Get a summary of best practices for Freqtrade Hyperopt, common issues, and CLI examples."""
    content = {
        "summary": "Summary of Freqtrade Hyperopt best practices.",
        "details": [
            "Use a realistic timerange: Don't optimize for a few days. Use at least 1-3 months of data, ideally more.",
            "Avoid overfitting: Don't use too many parameters or too wide ranges. Focus on parameters that make logical sense for your strategy.",
            "Sufficient epochs: Run enough epochs for the optimizer to converge (e.g., 100-1000+, depending on complexity).",
            "Meaningful objective function: Optimize for a metric that reflects your trading goals (e.g., `SortinoHyperOptLoss`, `SharpeHyperOptLossDaily`, `ExpectancyHyperOptLoss`).",
            "Regular re-optimization: Market conditions change. Re-optimize your parameters periodically.",
            "Spaces to optimize: 'buy', 'sell', 'protection', 'roi', 'stoploss', 'trailing'.",
            "Parameter types: Categorical (e.g., true/false), IntParameter, RealParameter, SKDecimalParameter.",
            "Consider `plot-dataframe` and `plot-profit` during hyperopt runs for visual feedback (if running locally)."
        ],
        "common_issues": [
            "Hyperopt takes too long: Reduce parameter space, use a smaller timerange for initial exploration, or use a more powerful machine.",
            "Results are not improving: Check your objective function, parameter ranges, and strategy logic.",
            "Overfitting: Results look great in hyperopt but perform poorly in backtesting/live. Simplify your parameter space or use more robust optimization techniques."
        ],
        "cli_examples": [
            "freqtrade hyperopt --config config.json --strategy MyStrategy --hyperopt-loss SharpeHyperOptLossDaily --epochs 100 --spaces roi stoploss",
            "freqtrade hyperopt --hyperopt MyHyperopt --epochs 500 --timerange 20230101-20231231"
        ],
        "reference": "https://www.freqtrade.io/en/stable/hyperoptimization/"
    }
    return content

@mcp_server.tool("freqtrade.knowledge.freqAiOverview")
def freqtrade_freqai_overview() -> Dict[str, Any]:
    """Get an overview of FreqAI, its features, setup requirements, usage, modern vs. legacy considerations, and example model types."""
    content = {
        "summary": "FreqAI is Freqtrade's machine learning module, allowing for predictive trading models.",
        "features": [
            "Integration with popular ML libraries (Scikit-learn, Keras/TensorFlow, PyTorch, LightGBM, CatBoost, XGBoost).",
            "Customizable data splitting and feature engineering.",
            "Live prediction and retraining capabilities.",
            "Support for various model types (classification, regression).",
            "Advanced outlier detection and data drift analysis."
        ],
        "setup_requirements": [
            "Ensure Freqtrade is installed with FreqAI dependencies (`pip install -r requirements-freqai.txt`).",
            "Configure `freqai` section in your `config.json`.",
            "Develop or adapt a strategy to work with FreqAI (implement `populate_any_indicators`, `feature_engineering_standard`, etc.).",
            "Sufficient historical data for training."
        ],
        "usage_flow": [
            "1. Data download and preparation.",
            "2. Feature engineering within your strategy.",
            "3. Model training (either manually via CLI or automatically by the bot).",
            "4. Model deployment for live predictions.",
            "5. Periodic retraining and monitoring."
        ],
        "modern_vs_legacy_freqai": "Always prefer Modern FreqAI. Legacy FreqAI is deprecated and has significant limitations. Modern FreqAI offers more flexibility, better data handling, and advanced features.",
        "common_pitfalls": [
            "Data leakage: Accidentally using future information during training.",
            "Overfitting: Models perform well on training data but poorly on unseen data.",
            "Insufficient data: Not enough historical data for robust model training.",
            "Poor feature engineering: Features do not capture predictive signals.",
            "Ignoring model interpretability: Not understanding why the model makes certain predictions."
        ],
        "example_model_types": ["RandomForestClassifier", "GradientBoostingClassifier", "LGBMClassifier", "CatBoostClassifier", "XGBClassifier", "Keras/TensorFlow (Sequential models)", "PyTorch models"],
        "cli_examples_freqai": [
            "freqtrade trade --config config.json --strategy MyFreqAIStrategy",
            "freqtrade list-freqaimodels --config config.json --strategy-list MyFreqAIStrategy",
            "freqtrade download-data --timerange 20210101- --pairs ETH/BTC XRP/BTC --exchange binance",
            "# Training is often done by the bot based on config, but manual triggers might be possible or via specific scripts."
        ],
        "reference": "https://www.freqtrade.io/en/stable/freqai/"
    }
    return content

# --- Source Code Exploration Tools ---

@mcp_server.tool("freqtrade.source.getFileContent")
async def freqtrade_get_file_content(path: str) -> Dict[str, str]:
    """Reads the content of a specified file from the Freqtrade source code (/freqtrade).
    
    Args:
        path: Relative path within the Freqtrade source repository (e.g., 'freqtrade/main.py', 'docs/docs/configuration.md').
    """
    target_file = os.path.join(FREQTRADE_SRC_PATH, path.lstrip('/'))
    
    if not os.path.abspath(target_file).startswith(os.path.abspath(FREQTRADE_SRC_PATH)):
        logger.warning(f"Attempt to access path outside FREQTRADE_SRC_PATH: {path}")
        return {"error": "Access to path outside the source repository is forbidden."}

    if not os.path.exists(target_file) or not os.path.isfile(target_file):
        logger.warning(f"File not found or not a file: {target_file}")
        return {"error": f"File not found: {path}"}
        
    try:
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.read()
        logger.info(f"Successfully read file: {target_file}", extra={"props": {"file_path": path}})
        return {"path": path, "content": content}
    except Exception as e:
        logger.error(f"Error reading file {target_file}: {e}", exc_info=True)
        return {"error": f"Error reading file: {str(e)}"}

@mcp_server.tool("freqtrade.source.listDirectory")
async def freqtrade_list_directory(path: str) -> Dict[str, Union[str, List[str]]]:
    """Lists contents of a directory within the Freqtrade source code (/freqtrade).
    
    Args:
        path: Relative path within the Freqtrade source repository.
    """
    target_dir = os.path.join(FREQTRADE_SRC_PATH, path.lstrip('/'))

    if not os.path.abspath(target_dir).startswith(os.path.abspath(FREQTRADE_SRC_PATH)):
        logger.warning(f"Attempt to access path outside FREQTRADE_SRC_PATH: {path}")
        return {"error": "Access to path outside the source repository is forbidden."}

    if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
        logger.warning(f"Directory not found or not a directory: {target_dir}")
        return {"error": f"Directory not found: {path}"}

    try:
        contents = os.listdir(target_dir)
        dirs = [item for item in contents if os.path.isdir(os.path.join(target_dir, item))]
        files = [item for item in contents if os.path.isfile(os.path.join(target_dir, item))]
        
        logger.info(f"Listed directory: {target_dir}", extra={"props": {"dir_path": path, "dirs_count": len(dirs), "files_count": len(files)}})
        return {
            "path": path,
            "directories": sorted(dirs),
            "files": sorted(files)
        }
    except Exception as e:
        logger.error(f"Error listing directory {target_dir}: {e}", exc_info=True)
        return {"error": f"Error listing directory: {str(e)}"}

@mcp_server.tool("freqtrade.cli.runInfoCommand")
async def freqtrade_run_cli_info_command(subcommand: str, options: Optional[List[str]] = None) -> Dict[str, Any]:
    """Run informational Freqtrade CLI commands within the container.
    
    Args:
        subcommand: The Freqtrade subcommand (e.g., 'list-exchanges', 'list-strategies', 'show-config').
        options: Additional command-line options.
    
    Note: Only informational commands are allowed.
    """
    ALLOWED_INFO_SUBCOMMANDS = [
        'list-exchanges', 'list-markets', 'list-pairs', 'list-strategies',
        'list-hyperoptloss', 'list-freqaimodels', 'list-timeframes', 
        'show-config', '--version', '--help'
    ]
    
    if subcommand not in ALLOWED_INFO_SUBCOMMANDS:
        logger.warning(f"Attempted to run disallowed command: {subcommand}")
        return {"error": f"Command '{subcommand}' is not allowed. Only informational commands are permitted."}
    
    # Build the full command
    full_command = f"freqtrade {subcommand}"
    if options:
        sanitized_options = [shlex.quote(opt) for opt in options]
        full_command += " " + " ".join(sanitized_options)
    
    logger.info(f"Running Freqtrade CLI command: {full_command}")
    
    return_code, stdout, stderr = await run_local_command(full_command, working_dir=FREQTRADE_SRC_PATH)
    
    if return_code == 0:
        return {"status": "success", "subcommand": subcommand, "options": options, "output": stdout}
    else:
        return {"status": "error", "subcommand": subcommand, "options": options, "error_message": stderr, "output": stdout}


# --- Health Check ---
async def health_check(request):
    logger.debug("Health check requested")
    repo_accessible = os.path.exists(os.path.join(FREQTRADE_SRC_PATH, "LICENSE"))
    status = "healthy" if repo_accessible else "degraded"
    
    return JSONResponse({
        "status": status, 
        "service": SERVICE_NAME, 
        "timestamp": dt.now().isoformat(),
        "checks": {
            "freqtrade_repo_access": "accessible" if repo_accessible else "inaccessible"
        }
    })

# --- Main Execution ---
if __name__ == "__main__":
    logger.info(f"Starting {SERVICE_NAME} on port {MCP_PORT}")
    
    # Get the SSE app from FastMCP
    app = mcp_server.sse_app()
    
    # Add health check route
    if not any(r.path == "/health" for r in getattr(app, 'routes', [])):
        if hasattr(app, 'routes') and isinstance(app.routes, list):
            app.routes.append(Route("/health", health_check))
            logger.info("Health check route added")
    
    # Run the server
    log_level_env = os.getenv("LOG_LEVEL", "INFO").lower()
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT, log_level=log_level_env)
# 17_crypto_trader_mcp (Port 8017)

## Purpose
Comprehensive cryptocurrency trading and market analysis service that provides real-time market data, technical analysis, trading signals, portfolio management, and risk assessment tools. Designed to work seamlessly with Claude Code for intelligent trading decisions.

Tools are organized under the `crypto.*` namespace.

## Namespaced Tools

### Market Data
- **`crypto.market.price(symbols: list[str], exchange: str = "binance") -> dict`**: 
  Get real-time price data for cryptocurrencies.

- **`crypto.market.ohlcv(symbol: str, timeframe: str = "1h", limit: int = 100) -> dict`**: 
  Get OHLCV (Open, High, Low, Close, Volume) candlestick data.

- **`crypto.market.orderbook(symbol: str, limit: int = 20) -> dict`**: 
  Get current order book depth.

- **`crypto.market.trades(symbol: str, limit: int = 100) -> dict`**: 
  Get recent trades for a symbol.

### Technical Analysis
- **`crypto.ta.indicators(symbol: str, indicators: list[str], timeframe: str = "1h") -> dict`**: 
  Calculate technical indicators (RSI, MACD, BB, EMA, etc.).

- **`crypto.ta.patterns(symbol: str, timeframe: str = "1h") -> dict`**: 
  Detect chart patterns (head & shoulders, triangles, etc.).

- **`crypto.ta.signals(symbol: str, strategy: str = "multi") -> dict`**: 
  Generate trading signals based on technical analysis.

### Trading Operations
- **`crypto.trade.simulate(symbol: str, side: str, amount: float, price: float = None) -> dict`**: 
  Simulate a trade without executing (paper trading).

- **`crypto.trade.backtest(strategy: dict, symbol: str, start_date: str, end_date: str) -> dict`**: 
  Backtest a trading strategy on historical data.

- **`crypto.trade.risk(position: dict, stop_loss: float, take_profit: float) -> dict`**: 
  Calculate risk metrics for a position.

### Portfolio Management
- **`crypto.portfolio.balance(exchange: str = "all") -> dict`**: 
  Get current portfolio balances across exchanges.

- **`crypto.portfolio.performance(period: str = "24h") -> dict`**: 
  Calculate portfolio performance metrics.

- **`crypto.portfolio.allocation() -> dict`**: 
  Analyze portfolio allocation and suggest rebalancing.

- **`crypto.portfolio.history(days: int = 30) -> dict`**: 
  Get portfolio value history.

### Market Analysis
- **`crypto.analysis.sentiment(symbol: str = None) -> dict`**: 
  Analyze market sentiment from various sources.

- **`crypto.analysis.correlation(symbols: list[str], period: str = "30d") -> dict`**: 
  Calculate correlation between different cryptocurrencies.

- **`crypto.analysis.volatility(symbol: str, period: str = "24h") -> dict`**: 
  Calculate volatility metrics.

- **`crypto.analysis.trends() -> dict`**: 
  Identify trending cryptocurrencies and sectors.

### DeFi Tools
- **`crypto.defi.yields() -> dict`**: 
  Get current DeFi yield farming opportunities.

- **`crypto.defi.liquidity(protocol: str, pair: str) -> dict`**: 
  Check liquidity pool information.

- **`crypto.defi.gas() -> dict`**: 
  Get current gas prices across networks.

### Alerts & Monitoring
- **`crypto.alerts.create(condition: dict, action: str) -> dict`**: 
  Create price or indicator alerts.

- **`crypto.alerts.list() -> dict`**: 
  List active alerts.

- **`crypto.monitor.whale(symbol: str = None) -> dict`**: 
  Monitor large transactions (whale activity).

## Container Layout
```
17_crypto_trader_mcp/
├── Dockerfile
├── entrypoint.sh
├── requirements.txt
├── mcp_server.py
├── config/
│   └── exchanges.yaml
├── data/
│   ├── cache/
│   └── historical/
├── analyzers/
│   ├── technical.py
│   ├── sentiment.py
│   └── patterns.py
├── connectors/
│   ├── binance.py
│   ├── coinbase.py
│   └── coingecko.py
├── strategies/
│   ├── base.py
│   └── examples/
└── README.md
```

## Key Features

1. **Multi-Exchange Support**: Binance, Coinbase, Kraken, etc.
2. **Real-time Data**: WebSocket feeds for live market data
3. **Technical Indicators**: 50+ indicators available
4. **Pattern Recognition**: ML-based chart pattern detection
5. **Risk Management**: Position sizing, stop-loss calculations
6. **Claude Integration**: Natural language trading interface

## Implementation Details
- **Framework:** Python with FastMCP
- **Market Data:** ccxt library for exchange connectivity
- **Technical Analysis:** TA-Lib, pandas-ta
- **Real-time:** WebSocket connections
- **Caching:** Redis for performance
- **Claude Bridge:** Direct integration with Claude Code

## Operating Principles
1. **Real-time Focus**: Live data with minimal latency
2. **Exchange Agnostic**: Works with multiple exchanges
3. **Risk First**: Built-in risk management tools
4. **Claude Synergy**: Designed for natural language interaction
5. **Privacy**: No trade execution without explicit approval

## Configuration
- `MCP_PORT=8017`
- `DATA_DIR=/workspace/crypto_data`
- `ENABLE_PAPER_TRADING=true`
- `DEFAULT_EXCHANGE=binance`
- `CACHE_TTL=60` # seconds
- `MAX_HISTORICAL_DAYS=365`
- `REQUIRE_TRADE_APPROVAL=true`

## API Keys (Optional)
- `BINANCE_API_KEY` # For authenticated endpoints
- `BINANCE_SECRET_KEY`
- `COINGECKO_API_KEY` # For higher rate limits

## Integration with Other Services
- **Freqtrade MCP**: Share strategies and backtest results
- **Documentation MCP**: Auto-document trading strategies
- **Secrets MCP**: Secure storage of API keys
- **AI Models MCP**: Advanced market predictions

## Security Considerations
- API keys stored securely in secrets service
- No automatic trade execution by default
- All trades require explicit approval
- Rate limiting to prevent API abuse
- Encrypted storage of sensitive data

## Example Claude Interactions
```
"What's the current price of BTC and ETH?"
"Show me the RSI and MACD for BTC on the 4h timeframe"
"Analyze my portfolio performance over the last week"
"What are the top trending cryptocurrencies today?"
"Backtest a simple RSI strategy on ETH for the last month"
"Alert me when BTC crosses above $50,000"
"What's the current market sentiment for altcoins?"
```
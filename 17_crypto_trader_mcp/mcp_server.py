import os
import logging
from typing import Optional, List, Dict, Any
import json
from datetime import datetime, timedelta
import asyncio
from decimal import Decimal

import ccxt
import pandas as pd
import numpy as np
from ta import add_all_ta_features
from ta.utils import dropna
import yfinance as yf

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
MCP_PORT = int(os.getenv("MCP_PORT", 8017))
DEFAULT_EXCHANGE = os.getenv("DEFAULT_EXCHANGE", "binance")
ENABLE_PAPER_TRADING = os.getenv("ENABLE_PAPER_TRADING", "true").lower() == "true"
REQUIRE_TRADE_APPROVAL = os.getenv("REQUIRE_TRADE_APPROVAL", "true").lower() == "true"

# Initialize MCP server
mcp = FastMCP("Crypto Trader MCP Server")

# Exchange connections (lazy loaded)
exchanges = {}

# Paper trading portfolio
paper_portfolio = {
    "USDT": 10000.0,  # Starting balance
    "positions": {},
    "trades": [],
    "total_value": 10000.0
}

def get_exchange(exchange_name: str = DEFAULT_EXCHANGE) -> ccxt.Exchange:
    """Get or create exchange connection"""
    if exchange_name not in exchanges:
        exchange_class = getattr(ccxt, exchange_name)
        exchanges[exchange_name] = exchange_class({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
            }
        })
    return exchanges[exchange_name]

@mcp.tool("crypto.market.price")
async def get_market_price(symbols: List[str], exchange: str = DEFAULT_EXCHANGE) -> Dict[str, Any]:
    """
    Get real-time price data for cryptocurrencies.
    
    Args:
        symbols: List of symbols (e.g., ["BTC/USDT", "ETH/USDT"])
        exchange: Exchange to use (default: binance)
        
    Returns:
        Current prices, 24h change, volume
    """
    try:
        ex = get_exchange(exchange)
        tickers = ex.fetch_tickers(symbols)
        
        result = {}
        for symbol, ticker in tickers.items():
            result[symbol] = {
                "price": ticker['last'],
                "bid": ticker['bid'],
                "ask": ticker['ask'],
                "change_24h": ticker['percentage'],
                "volume_24h": ticker['quoteVolume'],
                "high_24h": ticker['high'],
                "low_24h": ticker['low'],
                "timestamp": ticker['timestamp']
            }
        
        return {
            "exchange": exchange,
            "prices": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching prices: {str(e)}")
        return {"error": str(e)}

@mcp.tool("crypto.market.ohlcv")
async def get_ohlcv_data(
    symbol: str, 
    timeframe: str = "1h", 
    limit: int = 100,
    exchange: str = DEFAULT_EXCHANGE
) -> Dict[str, Any]:
    """
    Get OHLCV candlestick data.
    
    Args:
        symbol: Trading pair (e.g., "BTC/USDT")
        timeframe: Candle timeframe (1m, 5m, 15m, 1h, 4h, 1d)
        limit: Number of candles to return
        exchange: Exchange to use
        
    Returns:
        OHLCV data with timestamps
    """
    try:
        ex = get_exchange(exchange)
        ohlcv = ex.fetch_ohlcv(symbol, timeframe, limit=limit)
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "data": df.to_dict('records'),
            "latest": {
                "open": float(df.iloc[-1]['open']),
                "high": float(df.iloc[-1]['high']),
                "low": float(df.iloc[-1]['low']),
                "close": float(df.iloc[-1]['close']),
                "volume": float(df.iloc[-1]['volume'])
            }
        }
    except Exception as e:
        logger.error(f"Error fetching OHLCV: {str(e)}")
        return {"error": str(e)}

@mcp.tool("crypto.ta.indicators")
async def calculate_indicators(
    symbol: str,
    indicators: List[str],
    timeframe: str = "1h",
    period: int = 100,
    exchange: str = DEFAULT_EXCHANGE
) -> Dict[str, Any]:
    """
    Calculate technical indicators.
    
    Args:
        symbol: Trading pair
        indicators: List of indicators (RSI, MACD, BB, EMA, SMA, etc.)
        timeframe: Timeframe for analysis
        period: Number of periods to analyze
        exchange: Exchange to use
        
    Returns:
        Calculated indicator values
    """
    try:
        # Get OHLCV data
        ex = get_exchange(exchange)
        ohlcv = ex.fetch_ohlcv(symbol, timeframe, limit=period + 50)  # Extra for indicator calculation
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df = dropna(df)
        
        # Add all technical indicators
        df = add_all_ta_features(
            df, open="open", high="high", low="low", close="close", volume="volume"
        )
        
        # Extract requested indicators
        result = {
            "symbol": symbol,
            "timeframe": timeframe,
            "latest_price": float(df.iloc[-1]['close']),
            "indicators": {}
        }
        
        # Map common indicator names
        indicator_map = {
            "RSI": "momentum_rsi",
            "MACD": ["trend_macd", "trend_macd_signal", "trend_macd_diff"],
            "BB": ["volatility_bbh", "volatility_bbl", "volatility_bbm"],
            "EMA": "trend_ema_fast",
            "SMA": "trend_sma_fast",
            "ATR": "volatility_atr",
            "ADX": "trend_adx",
            "STOCH": ["momentum_stoch", "momentum_stoch_signal"]
        }
        
        for indicator in indicators:
            if indicator in indicator_map:
                if isinstance(indicator_map[indicator], list):
                    result["indicators"][indicator] = {}
                    for col in indicator_map[indicator]:
                        if col in df.columns:
                            result["indicators"][indicator][col.split('_')[-1]] = float(df.iloc[-1][col])
                else:
                    col = indicator_map[indicator]
                    if col in df.columns:
                        result["indicators"][indicator] = float(df.iloc[-1][col])
        
        return result
    except Exception as e:
        logger.error(f"Error calculating indicators: {str(e)}")
        return {"error": str(e)}

@mcp.tool("crypto.ta.signals")
async def generate_signals(
    symbol: str,
    strategy: str = "multi",
    timeframe: str = "1h",
    exchange: str = DEFAULT_EXCHANGE
) -> Dict[str, Any]:
    """
    Generate trading signals based on technical analysis.
    
    Args:
        symbol: Trading pair
        strategy: Signal strategy (multi, rsi, macd, trend)
        timeframe: Timeframe for analysis
        exchange: Exchange to use
        
    Returns:
        Trading signals and confidence scores
    """
    try:
        # Calculate indicators
        indicators = await calculate_indicators(
            symbol, 
            ["RSI", "MACD", "BB", "EMA", "SMA", "ADX"],
            timeframe,
            exchange=exchange
        )
        
        if "error" in indicators:
            return indicators
        
        signals = {
            "symbol": symbol,
            "timeframe": timeframe,
            "price": indicators["latest_price"],
            "signals": {},
            "overall": "NEUTRAL",
            "confidence": 0.5
        }
        
        ind = indicators["indicators"]
        
        # RSI Signal
        if "RSI" in ind:
            rsi = ind["RSI"]
            if rsi < 30:
                signals["signals"]["RSI"] = {"signal": "BUY", "value": rsi, "reason": "Oversold"}
            elif rsi > 70:
                signals["signals"]["RSI"] = {"signal": "SELL", "value": rsi, "reason": "Overbought"}
            else:
                signals["signals"]["RSI"] = {"signal": "NEUTRAL", "value": rsi}
        
        # MACD Signal
        if "MACD" in ind:
            macd_diff = ind["MACD"].get("diff", 0)
            if macd_diff > 0:
                signals["signals"]["MACD"] = {"signal": "BUY", "value": macd_diff, "reason": "Bullish crossover"}
            elif macd_diff < 0:
                signals["signals"]["MACD"] = {"signal": "SELL", "value": macd_diff, "reason": "Bearish crossover"}
            else:
                signals["signals"]["MACD"] = {"signal": "NEUTRAL", "value": macd_diff}
        
        # Calculate overall signal
        buy_signals = sum(1 for s in signals["signals"].values() if s["signal"] == "BUY")
        sell_signals = sum(1 for s in signals["signals"].values() if s["signal"] == "SELL")
        total_signals = len(signals["signals"])
        
        if total_signals > 0:
            if buy_signals > sell_signals and buy_signals / total_signals > 0.6:
                signals["overall"] = "BUY"
                signals["confidence"] = buy_signals / total_signals
            elif sell_signals > buy_signals and sell_signals / total_signals > 0.6:
                signals["overall"] = "SELL"
                signals["confidence"] = sell_signals / total_signals
        
        return signals
    except Exception as e:
        logger.error(f"Error generating signals: {str(e)}")
        return {"error": str(e)}

@mcp.tool("crypto.trade.simulate")
async def simulate_trade(
    symbol: str,
    side: str,
    amount: float,
    price: Optional[float] = None,
    exchange: str = DEFAULT_EXCHANGE
) -> Dict[str, Any]:
    """
    Simulate a trade (paper trading).
    
    Args:
        symbol: Trading pair
        side: "buy" or "sell"
        amount: Amount to trade
        price: Limit price (optional, uses market price if not provided)
        exchange: Exchange to simulate on
        
    Returns:
        Simulated trade results
    """
    if not ENABLE_PAPER_TRADING:
        return {"error": "Paper trading is disabled"}
    
    try:
        # Get current price if not provided
        if price is None:
            price_data = await get_market_price([symbol], exchange)
            if "error" in price_data:
                return price_data
            price = price_data["prices"][symbol]["price"]
        
        base, quote = symbol.split('/')
        
        if side.lower() == "buy":
            # Check if we have enough quote currency
            cost = amount * price
            if paper_portfolio.get(quote, 0) < cost:
                return {"error": f"Insufficient {quote} balance. Required: {cost}, Available: {paper_portfolio.get(quote, 0)}"}
            
            # Execute buy
            paper_portfolio[quote] = paper_portfolio.get(quote, 0) - cost
            paper_portfolio["positions"][base] = paper_portfolio["positions"].get(base, 0) + amount
            
            trade = {
                "id": len(paper_portfolio["trades"]) + 1,
                "symbol": symbol,
                "side": "buy",
                "amount": amount,
                "price": price,
                "cost": cost,
                "timestamp": datetime.now().isoformat()
            }
            
        else:  # sell
            # Check if we have enough base currency
            if paper_portfolio["positions"].get(base, 0) < amount:
                return {"error": f"Insufficient {base} balance. Available: {paper_portfolio['positions'].get(base, 0)}"}
            
            # Execute sell
            revenue = amount * price
            paper_portfolio["positions"][base] -= amount
            if paper_portfolio["positions"][base] == 0:
                del paper_portfolio["positions"][base]
            paper_portfolio[quote] = paper_portfolio.get(quote, 0) + revenue
            
            trade = {
                "id": len(paper_portfolio["trades"]) + 1,
                "symbol": symbol,
                "side": "sell",
                "amount": amount,
                "price": price,
                "revenue": revenue,
                "timestamp": datetime.now().isoformat()
            }
        
        paper_portfolio["trades"].append(trade)
        
        return {
            "trade": trade,
            "portfolio": {
                "balances": {k: v for k, v in paper_portfolio.items() if k not in ["positions", "trades", "total_value"]},
                "positions": paper_portfolio["positions"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error simulating trade: {str(e)}")
        return {"error": str(e)}

@mcp.tool("crypto.portfolio.balance")
async def get_portfolio_balance(exchange: str = "paper") -> Dict[str, Any]:
    """
    Get current portfolio balances.
    
    Args:
        exchange: Exchange name or "paper" for paper trading
        
    Returns:
        Current balances and positions
    """
    if exchange == "paper":
        # Calculate total portfolio value
        total_value = paper_portfolio.get("USDT", 0)
        
        # Add position values
        for asset, amount in paper_portfolio["positions"].items():
            try:
                price_data = await get_market_price([f"{asset}/USDT"])
                if "prices" in price_data and f"{asset}/USDT" in price_data["prices"]:
                    price = price_data["prices"][f"{asset}/USDT"]["price"]
                    total_value += amount * price
            except:
                pass
        
        return {
            "exchange": "paper",
            "balances": {k: v for k, v in paper_portfolio.items() if k not in ["positions", "trades", "total_value"]},
            "positions": paper_portfolio["positions"],
            "total_value_usdt": total_value,
            "trades_count": len(paper_portfolio["trades"])
        }
    else:
        return {"error": "Real exchange connections not implemented yet"}

@mcp.tool("crypto.portfolio.performance")
async def get_portfolio_performance(period: str = "all") -> Dict[str, Any]:
    """
    Calculate portfolio performance metrics.
    
    Args:
        period: Performance period (24h, 7d, 30d, all)
        
    Returns:
        Performance metrics including PnL, returns, etc.
    """
    try:
        current_balance = await get_portfolio_balance()
        if "error" in current_balance:
            return current_balance
        
        initial_value = 10000.0  # Initial portfolio value
        current_value = current_balance["total_value_usdt"]
        
        pnl = current_value - initial_value
        pnl_percent = (pnl / initial_value) * 100
        
        # Calculate trade statistics
        trades = paper_portfolio["trades"]
        winning_trades = 0
        losing_trades = 0
        
        for i, trade in enumerate(trades):
            if trade["side"] == "sell" and i > 0:
                # Look for corresponding buy trade
                for j in range(i-1, -1, -1):
                    if trades[j]["side"] == "buy" and trades[j]["symbol"] == trade["symbol"]:
                        if trade["price"] > trades[j]["price"]:
                            winning_trades += 1
                        else:
                            losing_trades += 1
                        break
        
        total_completed_trades = winning_trades + losing_trades
        win_rate = (winning_trades / total_completed_trades * 100) if total_completed_trades > 0 else 0
        
        return {
            "period": period,
            "initial_value": initial_value,
            "current_value": current_value,
            "pnl_usdt": pnl,
            "pnl_percent": pnl_percent,
            "total_trades": len(trades),
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "current_positions": len(paper_portfolio["positions"])
        }
        
    except Exception as e:
        logger.error(f"Error calculating performance: {str(e)}")
        return {"error": str(e)}

@mcp.tool("crypto.analysis.trends")
async def analyze_trends() -> Dict[str, Any]:
    """
    Identify trending cryptocurrencies.
    
    Returns:
        Top gainers, losers, and trending coins
    """
    try:
        ex = get_exchange()
        tickers = ex.fetch_tickers()
        
        # Filter USDT pairs
        usdt_pairs = {k: v for k, v in tickers.items() if k.endswith('/USDT')}
        
        # Sort by 24h change
        sorted_by_change = sorted(
            usdt_pairs.items(), 
            key=lambda x: x[1]['percentage'] if x[1]['percentage'] else 0,
            reverse=True
        )
        
        # Get top gainers and losers
        top_gainers = []
        top_losers = []
        
        for symbol, ticker in sorted_by_change[:10]:
            if ticker['percentage'] and ticker['percentage'] > 0:
                top_gainers.append({
                    "symbol": symbol,
                    "price": ticker['last'],
                    "change_24h": ticker['percentage'],
                    "volume_24h": ticker['quoteVolume']
                })
        
        for symbol, ticker in sorted_by_change[-10:]:
            if ticker['percentage'] and ticker['percentage'] < 0:
                top_losers.append({
                    "symbol": symbol,
                    "price": ticker['last'],
                    "change_24h": ticker['percentage'],
                    "volume_24h": ticker['quoteVolume']
                })
        
        # High volume coins
        sorted_by_volume = sorted(
            usdt_pairs.items(),
            key=lambda x: x[1]['quoteVolume'] if x[1]['quoteVolume'] else 0,
            reverse=True
        )
        
        high_volume = []
        for symbol, ticker in sorted_by_volume[:10]:
            high_volume.append({
                "symbol": symbol,
                "price": ticker['last'],
                "volume_24h": ticker['quoteVolume'],
                "change_24h": ticker['percentage']
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "top_gainers": top_gainers[:5],
            "top_losers": top_losers[:5],
            "high_volume": high_volume[:5],
            "market_summary": {
                "total_coins": len(usdt_pairs),
                "gaining": len([t for t in usdt_pairs.values() if t.get('percentage', 0) > 0]),
                "losing": len([t for t in usdt_pairs.values() if t.get('percentage', 0) < 0])
            }
        }
        
    except Exception as e:
        logger.error(f"Error analyzing trends: {str(e)}")
        return {"error": str(e)}

@mcp.tool("crypto.analysis.sentiment")
async def analyze_sentiment(symbol: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze market sentiment (simplified version).
    
    Args:
        symbol: Specific symbol to analyze (optional)
        
    Returns:
        Sentiment indicators and fear/greed index
    """
    try:
        # Simplified sentiment based on market movements
        trends = await analyze_trends()
        if "error" in trends:
            return trends
        
        market = trends["market_summary"]
        gaining_ratio = market["gaining"] / market["total_coins"] if market["total_coins"] > 0 else 0.5
        
        # Simple fear/greed calculation
        if gaining_ratio > 0.7:
            sentiment = "Extreme Greed"
            score = 80 + (gaining_ratio - 0.7) * 66.67
        elif gaining_ratio > 0.6:
            sentiment = "Greed"
            score = 60 + (gaining_ratio - 0.6) * 200
        elif gaining_ratio > 0.4:
            sentiment = "Neutral"
            score = 40 + (gaining_ratio - 0.4) * 100
        elif gaining_ratio > 0.3:
            sentiment = "Fear"
            score = 20 + (gaining_ratio - 0.3) * 200
        else:
            sentiment = "Extreme Fear"
            score = gaining_ratio * 66.67
        
        result = {
            "overall_sentiment": sentiment,
            "fear_greed_index": round(score, 2),
            "market_metrics": {
                "gaining_coins_ratio": round(gaining_ratio, 3),
                "total_coins_analyzed": market["total_coins"],
                "bullish_coins": market["gaining"],
                "bearish_coins": market["losing"]
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Add symbol-specific sentiment if requested
        if symbol:
            price_data = await get_market_price([symbol])
            if "prices" in price_data and symbol in price_data["prices"]:
                symbol_data = price_data["prices"][symbol]
                symbol_sentiment = "Bullish" if symbol_data["change_24h"] > 0 else "Bearish"
                result["symbol_sentiment"] = {
                    "symbol": symbol,
                    "sentiment": symbol_sentiment,
                    "change_24h": symbol_data["change_24h"],
                    "volume_24h": symbol_data["volume_24h"]
                }
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {str(e)}")
        return {"error": str(e)}

@mcp.tool("crypto.alerts.create")
async def create_alert(condition: Dict[str, Any], action: str = "notify") -> Dict[str, Any]:
    """
    Create a price or indicator alert.
    
    Args:
        condition: Alert condition (e.g., {"symbol": "BTC/USDT", "price": ">", "value": 50000})
        action: Action to take when triggered
        
    Returns:
        Alert confirmation
    """
    # Simplified alert creation (would need persistent storage in production)
    alert = {
        "id": f"alert_{datetime.now().timestamp()}",
        "condition": condition,
        "action": action,
        "created": datetime.now().isoformat(),
        "status": "active"
    }
    
    return {
        "alert": alert,
        "message": "Alert created successfully. Note: Alerts are not persistent in this demo version."
    }

# Health check endpoint
@mcp.tool("crypto.health")
async def health_check() -> Dict[str, Any]:
    """Check service health and available features."""
    return {
        "status": "healthy",
        "service": "crypto-trader-mcp",
        "version": "1.0.0",
        "features": {
            "market_data": True,
            "technical_analysis": True,
            "paper_trading": ENABLE_PAPER_TRADING,
            "real_trading": False,  # Not implemented for safety
            "alerts": True,
            "sentiment": True
        },
        "supported_exchanges": ["binance", "coinbase", "kraken"],
        "default_exchange": DEFAULT_EXCHANGE
    }

if __name__ == "__main__":
    # Run the MCP server
    import uvicorn
    app = mcp.sse_app()
    logger.info(f"Starting Crypto Trader MCP Server on port {MCP_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT, log_level="info")
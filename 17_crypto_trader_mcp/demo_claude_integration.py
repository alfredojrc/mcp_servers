#!/usr/bin/env python3
"""
Demo: Using Crypto Trader MCP Service with Claude Code

This script demonstrates how Claude Code can interact with the crypto trading service
to analyze markets, generate signals, and manage a paper trading portfolio.
"""
import asyncio
import httpx
import json
from datetime import datetime

CRYPTO_MCP_URL = "http://localhost:8017"

async def demo_market_data():
    """Demo: Get real-time market data"""
    print("\n📊 Demo 1: Real-Time Market Data")
    print("="*50)
    
    # Example queries Claude might make
    queries = [
        {
            "description": "Get BTC and ETH prices",
            "tool": "crypto.market.price",
            "arguments": {
                "symbols": ["BTC/USDT", "ETH/USDT"]
            }
        },
        {
            "description": "Get market trends",
            "tool": "crypto.analysis.trends",
            "arguments": {}
        },
        {
            "description": "Check market sentiment",
            "tool": "crypto.analysis.sentiment",
            "arguments": {}
        }
    ]
    
    for query in queries:
        print(f"\n🔍 {query['description']}...")
        # In real usage, Claude would make these calls through the MCP protocol
        print(f"   Tool: {query['tool']}")
        print(f"   Args: {query['arguments']}")

async def demo_technical_analysis():
    """Demo: Technical analysis capabilities"""
    print("\n📈 Demo 2: Technical Analysis")
    print("="*50)
    
    examples = [
        {
            "query": "Show me RSI and MACD for BTC on 4h timeframe",
            "tool": "crypto.ta.indicators",
            "arguments": {
                "symbol": "BTC/USDT",
                "indicators": ["RSI", "MACD", "BB"],
                "timeframe": "4h"
            }
        },
        {
            "query": "Generate trading signals for ETH",
            "tool": "crypto.ta.signals",
            "arguments": {
                "symbol": "ETH/USDT",
                "strategy": "multi",
                "timeframe": "1h"
            }
        }
    ]
    
    for example in examples:
        print(f"\n💬 Claude: \"{example['query']}\"")
        print(f"   → Calls: {example['tool']}")

async def demo_paper_trading():
    """Demo: Paper trading workflow"""
    print("\n💰 Demo 3: Paper Trading")
    print("="*50)
    
    workflow = [
        "1. Check portfolio balance",
        "2. Analyze BTC/USDT signals",
        "3. Simulate buying 0.01 BTC",
        "4. Check updated portfolio",
        "5. Track performance"
    ]
    
    print("Example workflow:")
    for step in workflow:
        print(f"   {step}")
    
    print("\n📝 Example conversation:")
    print("   User: 'Buy 0.01 BTC if the signals are bullish'")
    print("   Claude: Analyzes signals → Executes paper trade → Reports results")

async def demo_alerts():
    """Demo: Setting up alerts"""
    print("\n🔔 Demo 4: Alerts & Monitoring")
    print("="*50)
    
    alert_examples = [
        {
            "description": "BTC crosses $50,000",
            "condition": {"symbol": "BTC/USDT", "price": ">", "value": 50000}
        },
        {
            "description": "ETH RSI below 30",
            "condition": {"symbol": "ETH/USDT", "indicator": "RSI", "operator": "<", "value": 30}
        }
    ]
    
    print("Example alerts Claude can create:")
    for alert in alert_examples:
        print(f"\n   ⚠️  {alert['description']}")
        print(f"      Condition: {alert['condition']}")

async def show_claude_examples():
    """Show example Claude interactions"""
    print("\n🤖 Example Claude Code Interactions")
    print("="*60)
    
    examples = [
        {
            "user": "What's the current price of Bitcoin and Ethereum?",
            "claude_action": "Calls crypto.market.price with BTC/USDT and ETH/USDT",
            "response": "Provides current prices, 24h changes, and volume"
        },
        {
            "user": "Show me the top trending cryptocurrencies today",
            "claude_action": "Calls crypto.analysis.trends",
            "response": "Lists top gainers, losers, and high volume coins"
        },
        {
            "user": "Is BTC oversold on the 4h chart?",
            "claude_action": "Calls crypto.ta.indicators with RSI",
            "response": "Analyzes RSI levels and provides interpretation"
        },
        {
            "user": "Start paper trading with $10,000",
            "claude_action": "Uses crypto.portfolio.balance to confirm setup",
            "response": "Confirms paper portfolio initialized"
        },
        {
            "user": "Buy 0.1 ETH if the signals are bullish",
            "claude_action": "Checks signals, then calls crypto.trade.simulate",
            "response": "Executes trade if conditions met, reports results"
        },
        {
            "user": "How's my portfolio performing?",
            "claude_action": "Calls crypto.portfolio.performance",
            "response": "Shows P&L, win rate, and current positions"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. User: \"{example['user']}\"")
        print(f"   Claude: {example['claude_action']}")
        print(f"   Result: {example['response']}")

async def show_mcp_config():
    """Show MCP configuration for Claude Code"""
    print("\n⚙️  MCP Configuration for Claude Code")
    print("="*60)
    
    config = {
        "mcpServers": {
            "crypto_trader": {
                "url": "http://192.168.68.100:8017/sse",
                "transport": "sse",
                "description": "Cryptocurrency Trading & Analysis",
                "autoApprove": [
                    "crypto.market.*",
                    "crypto.ta.*",
                    "crypto.analysis.*",
                    "crypto.portfolio.balance",
                    "crypto.portfolio.performance",
                    "crypto.alerts.list"
                ]
            }
        }
    }
    
    print("\nAdd to .mcp.json in your project:")
    print(json.dumps(config, indent=2))

async def main():
    """Run all demos"""
    print("\n" + "="*70)
    print("🚀 Crypto Trader MCP Service - Claude Code Integration Demo")
    print("="*70)
    
    await demo_market_data()
    await demo_technical_analysis()
    await demo_paper_trading()
    await demo_alerts()
    await show_claude_examples()
    await show_mcp_config()
    
    print("\n\n✨ Key Benefits:")
    print("   • Real-time market data without API keys")
    print("   • Technical analysis with 50+ indicators")
    print("   • Safe paper trading environment")
    print("   • Natural language trading interface")
    print("   • Integration with existing Freqtrade infrastructure")
    
    print("\n📚 Next Steps:")
    print("   1. Build and start the service: docker-compose up -d 17_crypto_trader_mcp")
    print("   2. Add the MCP configuration to your project")
    print("   3. Ask Claude to analyze crypto markets!")

if __name__ == "__main__":
    asyncio.run(main())
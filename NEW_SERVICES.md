# New MCP Services Documentation

This document details the new MCP services added to the ecosystem: Documentation Management, Cryptocurrency Trading, and Vector Database.

## 11_documentation_mcp - Documentation Management Service

### Overview
A comprehensive documentation management service that provides search, CRUD operations, versioning, and web interface for project documentation.

### Port
- **Service Port**: 8011
- **Web Interface**: http://192.168.68.100:8011/

### Key Features
- Full-text search using Whoosh
- Document versioning with Git integration
- Markdown support with frontmatter metadata
- RESTful web interface
- Tag-based categorization
- Bulk operations support

### Available Tools
- `docs.search` - Search documentation by query, tags, or path
- `docs.create` - Create new documentation files
- `docs.read` - Read document content with metadata
- `docs.update` - Update existing documents
- `docs.delete` - Delete documents
- `docs.list` - List all documents with filtering
- `docs.list_versions` - View document version history
- `docs.revert` - Revert to previous versions
- `docs.bulk_update` - Update multiple documents
- `docs.export` - Export documentation sets

### Configuration
```yaml
environment:
  - MCP_PORT=8011
  - DOCS_ROOT=/workspace/docs
  - REQUIRE_APPROVAL=false
  - LOG_LEVEL=INFO
```

### Usage Example
```python
# Search for documentation
await docs.search(query="kubernetes deployment", tags=["k8s", "deployment"])

# Create new document
await docs.create(
    title="API Guide",
    content="# API Documentation\n...",
    tags=["api", "guide"],
    metadata={"author": "DevOps Team", "version": "1.0"}
)
```

## 17_crypto_trader_mcp - Cryptocurrency Trading Service

### Overview
A comprehensive cryptocurrency trading and analysis service with paper trading capabilities, technical indicators, and market analysis.

### Port
- **Service Port**: 8017

### Key Features
- Real-time market data (no API key required for public data)
- 50+ technical indicators via TA-Lib
- Paper trading simulation
- Multi-exchange support (Binance, Coinbase, Kraken, etc.)
- Market sentiment analysis
- Price alerts and monitoring

### Available Tools
- `crypto.market.price` - Get real-time cryptocurrency prices
- `crypto.market.orderbook` - Fetch order book data
- `crypto.market.ohlcv` - Get OHLCV candle data
- `crypto.ta.indicators` - Calculate technical indicators (RSI, MACD, etc.)
- `crypto.ta.signals` - Generate trading signals
- `crypto.analysis.trends` - Analyze market trends
- `crypto.analysis.sentiment` - Get market sentiment
- `crypto.trade.simulate` - Execute paper trades
- `crypto.portfolio.balance` - Check portfolio balance
- `crypto.portfolio.performance` - Get performance metrics
- `crypto.alerts.create` - Set price/indicator alerts
- `crypto.alerts.list` - List active alerts

### Configuration
```yaml
environment:
  - MCP_PORT=8017
  - DEFAULT_EXCHANGE=binance
  - ENABLE_PAPER_TRADING=true
  - REQUIRE_TRADE_APPROVAL=true
  - BINANCE_API_KEY=${BINANCE_API_KEY:-}  # Optional
  - BINANCE_SECRET_KEY=${BINANCE_SECRET_KEY:-}  # Optional
```

### Usage Example
```python
# Get Bitcoin price
await crypto.market.price(symbols=["BTC/USDT", "ETH/USDT"])

# Calculate technical indicators
await crypto.ta.indicators(
    symbol="BTC/USDT",
    indicators=["RSI", "MACD", "BB"],
    timeframe="4h"
)

# Simulate a trade
await crypto.trade.simulate(
    symbol="ETH/USDT",
    side="buy",
    amount=0.1,
    price="market"
)
```

## 18_vector_db_mcp - Vector Database Service

### Overview
A semantic search and vector database service using ChromaDB with local Sentence Transformers for embeddings. Provides RAG capabilities without external API dependencies.

### Port
- **Service Port**: 8018

### Key Features
- Local embeddings using Sentence Transformers
- Persistent vector storage with ChromaDB
- Collection management
- Cross-service data indexing
- Metadata filtering
- No external API requirements

### Available Tools
- `vector.collection.create` - Create a new vector collection
- `vector.collection.list` - List all collections
- `vector.collection.info` - Get collection details
- `vector.document.add` - Add documents with automatic embedding
- `vector.document.update` - Update existing documents
- `vector.document.delete` - Delete documents
- `vector.search.semantic` - Perform semantic search
- `vector.search.cross_service` - Search across multiple service collections
- `vector.index.service` - Index data from other MCP services

### Configuration
```yaml
environment:
  - MCP_PORT=8018
  - CHROMA_PERSIST_DIR=/app/data/chroma
  - EMBEDDING_MODEL=all-MiniLM-L6-v2
  - DEFAULT_COLLECTION=mcp_knowledge
```

### Usage Example
```python
# Create a collection
await vector.collection.create(
    name="project_docs",
    description="Project documentation vectors"
)

# Add documents
await vector.document.add(
    collection="project_docs",
    documents=["Guide to Kubernetes deployment", "Docker best practices"],
    metadatas=[
        {"type": "guide", "topic": "k8s"},
        {"type": "guide", "topic": "docker"}
    ]
)

# Semantic search
results = await vector.search.semantic(
    query="how to deploy containers",
    collection="project_docs",
    n_results=5
)

# Cross-service search
results = await vector.search.cross_service(
    query="authentication setup",
    services=["docs", "cmdb"],
    n_results=10
)
```

## Integration with Master Orchestrator

All three services are integrated with the master orchestrator (00_master_mcp) and accessible through the following namespaces:

- **Documentation**: `docs.*`
- **Crypto Trading**: `crypto.*`
- **Vector Database**: `vector.*`

### Claude Code Configuration

To use these services with Claude Code, ensure your `~/.mcp.json` includes:

```json
{
  "mcpServers": {
    "mcp": {
      "url": "http://192.168.68.100:8000/mcp/sse",
      "transport": "sse",
      "description": "Master MCP Orchestrator - Gateway to all services"
    }
  }
}
```

## Common Workflows

### 1. Documentation with Semantic Search
```python
# Index documentation in vector DB
await vector.index.service(
    service="docs",
    data_type="documentation",
    documents=[{
        "id": "guide-1",
        "title": "Kubernetes Setup",
        "content": "Complete guide to K8s...",
        "tags": ["k8s", "setup"]
    }]
)

# Search semantically
results = await vector.search.semantic(
    query="container orchestration setup",
    collection="docs_documentation"
)
```

### 2. Crypto Analysis Pipeline
```python
# Get market data
prices = await crypto.market.price(symbols=["BTC/USDT"])

# Analyze with indicators
analysis = await crypto.ta.indicators(
    symbol="BTC/USDT",
    indicators=["RSI", "MACD"],
    timeframe="1h"
)

# Store analysis in vector DB
await vector.document.add(
    collection="market_analysis",
    documents=[f"BTC analysis: {analysis}"],
    metadatas=[{
        "timestamp": datetime.now().isoformat(),
        "symbol": "BTC/USDT",
        "indicators": analysis
    }]
)
```

### 3. Documentation Discovery
```python
# Search across all documentation sources
results = await vector.search.cross_service(
    query="API authentication methods",
    services=["docs", "cmdb"],
    n_results=10
)
```

## Deployment

### Build and Deploy All New Services
```bash
# Build services
docker-compose build 11_documentation_mcp 17_crypto_trader_mcp 18_vector_db_mcp

# Deploy services
docker-compose up -d 11_documentation_mcp 17_crypto_trader_mcp 18_vector_db_mcp

# Verify health
curl http://192.168.68.100:8011/health  # Documentation
curl http://192.168.68.100:8017/health  # Crypto Trader
curl http://192.168.68.100:8018/health  # Vector DB
```

### Check Logs
```bash
docker-compose logs -f 11_documentation_mcp
docker-compose logs -f 17_crypto_trader_mcp
docker-compose logs -f 18_vector_db_mcp
```

## Performance Considerations

### Documentation Service
- Whoosh index rebuilds automatically
- Consider periodic optimization for large document sets
- Web interface caches static assets

### Crypto Trader
- Rate limits apply to exchange APIs
- Paper trading has no limits
- Technical indicators cached for repeated queries

### Vector Database
- ChromaDB handles millions of vectors efficiently
- Batch operations recommended for large datasets
- Collection-specific optimization available

## Security Notes

### Documentation Service
- Approval mechanism available (set `REQUIRE_APPROVAL=true`)
- Git integration tracks all changes
- Read/write permissions configurable

### Crypto Trader
- Paper trading enabled by default (no real money)
- API keys optional (only for authenticated endpoints)
- Trade approval required by default

### Vector Database
- All processing is local (no external APIs)
- Data persisted in Docker volumes
- No sensitive data transmitted

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 8011, 8017, 8018 are free
2. **Memory usage**: Vector DB may require 2GB+ RAM for large datasets
3. **Dependency installation**: Heavy ML dependencies may slow initial build

### Debug Commands
```bash
# Check service status
docker ps | grep -E "(documentation|crypto_trader|vector_db)_mcp"

# View service logs
docker logs mcp_servers_11_documentation_mcp_1
docker logs mcp_servers_17_crypto_trader_mcp_1
docker logs mcp_servers_18_vector_db_mcp_1

# Test connections
curl http://localhost:8011/health
curl http://localhost:8017/health
curl http://localhost:8018/health
```
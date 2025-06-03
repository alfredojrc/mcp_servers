# Vector Database Integration Guide

This guide shows how to integrate the Vector Database MCP service with other services in the MCP ecosystem.

## Quick Start

```bash
# Build and start the service
docker-compose up -d 18_vector_db_mcp

# Verify it's running
curl http://localhost:8018/health
```

## Integration Examples

### 1. Enhancing Documentation Service (11_documentation_mcp)

Add semantic search to the documentation service by indexing documents:

```python
# In 11_documentation_mcp/mcp_server.py, after creating a document:
@mcp.tool("docs.create")
async def create_document(title: str, content: str, ...):
    # ... existing code to create document ...
    
    # Index in vector database for semantic search
    await call_mcp_tool("vector.index.service", {
        "service": "docs",
        "data_type": "documentation",
        "documents": [{
            "id": doc_id,
            "title": title,
            "content": content,
            "path": file_path,
            "tags": tags,
            "created_at": created_at
        }]
    })
```

### 2. CMDB Semantic Search (12_cmdb_mcp)

Enable semantic search for configuration items:

```python
# Index CMDB entries when added/updated
await call_mcp_tool("vector.index.service", {
    "service": "cmdb",
    "data_type": "configuration_items",
    "documents": [{
        "id": f"cmdb_{hostname}",
        "title": hostname,
        "content": f"{hostname} {os_type} {os_version} {services}",
        "description": ssh_access_notes,
        "metadata": {
            "ip_address": ip_address,
            "services": services,
            "os_type": os_type
        }
    }]
})
```

### 3. Crypto Trading Context (17_crypto_trader_mcp)

Store market analysis and trading decisions for context:

```python
# Store market analysis
await call_mcp_tool("vector.document.add", {
    "collection": "market_analysis",
    "documents": [analysis_text],
    "metadatas": [{
        "timestamp": datetime.now().isoformat(),
        "symbol": "BTC/USDT",
        "indicators": {"RSI": 45.2, "MACD": 0.023},
        "sentiment": "neutral",
        "source": "crypto_trader_mcp"
    }]
})

# Search for similar market conditions
results = await call_mcp_tool("vector.search.semantic", {
    "query": "oversold conditions with bullish divergence",
    "collection": "market_analysis",
    "n_results": 5
})
```

### 4. Cross-Service Knowledge Search

Search across all indexed services:

```python
# Find information across docs, CMDB, and trading data
results = await call_mcp_tool("vector.search.cross_service", {
    "query": "kubernetes pod memory limits configuration",
    "services": ["docs", "cmdb", "k8s"],
    "n_results": 10
})
```

## Claude Code Configuration

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "vector": {
      "url": "http://192.168.68.100:8018/sse",
      "transport": "sse",
      "description": "Vector Database for Semantic Search",
      "autoApprove": [
        "vector.collection.list",
        "vector.collection.info",
        "vector.search.semantic",
        "vector.search.cross_service",
        "vector.document.add"
      ]
    }
  }
}
```

## Use Cases

### 1. Documentation Discovery
- "Find all docs about authentication"
- "Show me guides similar to the Kubernetes setup"
- "What documentation mentions rate limiting?"

### 2. Infrastructure Search
- "Find all services running Redis"
- "Show me containers with port 8080"
- "Which services are related to monitoring?"

### 3. Trading Knowledge Base
- "Find previous analyses for oversold conditions"
- "Show similar market setups to current BTC"
- "What strategies worked in high volatility?"

### 4. Workflow Context
- Store workflow results for future reference
- Find similar past workflows
- Build knowledge from workflow outcomes

## Performance Tips

1. **Batch Operations**: Add multiple documents at once
2. **Collection Strategy**: Use separate collections for different data types
3. **Metadata Filtering**: Use metadata to narrow searches
4. **Regular Cleanup**: Delete outdated documents to maintain performance

## Advanced Features

### Creating Custom Collections

```python
# Create a specialized collection
await call_mcp_tool("vector.collection.create", {
    "name": "incident_reports",
    "description": "System incidents and resolutions",
    "metadata": {
        "retention_days": 90,
        "index_type": "technical"
    }
})
```

### Similarity Thresholds

```python
# Search with similarity filtering
results = await call_mcp_tool("vector.search.semantic", {
    "query": "database connection timeout",
    "collection": "incident_reports",
    "n_results": 10,
    "where": {"severity": {"$in": ["high", "critical"]}}
})

# Filter by similarity score in your code
relevant_results = [r for r in results["results"] if r["similarity_score"] > 0.7]
```

## Monitoring

Check vector database health:

```bash
# Service health
curl http://localhost:8018/health

# Collection statistics
docker exec 18_vector_db_mcp python -c "
from mcp_server import chroma_client
for col in chroma_client.list_collections():
    print(f'{col.name}: {col.count()} documents')
"
```

## Troubleshooting

### Common Issues

1. **Slow searches**: Reduce collection size or use metadata filtering
2. **Memory usage**: Monitor with `docker stats 18_vector_db_mcp`
3. **Persistence**: Ensure volume is mounted correctly

### Debug Logging

```bash
# Enable debug logs
docker-compose exec 18_vector_db_mcp bash
export LOG_LEVEL=DEBUG
python mcp_server.py
```
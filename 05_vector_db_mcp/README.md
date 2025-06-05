# Vector Database MCP Service

A semantic search and embedding service using ChromaDB with local Sentence Transformers. This service provides vector database capabilities without requiring external API keys.

## Features

- **Semantic Search**: Find documents by meaning, not just keywords
- **Local Embeddings**: Uses Sentence Transformers (no API keys needed)
- **Collection Management**: Create and manage multiple vector collections
- **Cross-Service Search**: Index and search data from other MCP services
- **Persistent Storage**: ChromaDB persistence for data durability
- **MCP Protocol**: Full integration with the MCP ecosystem

## Architecture

```
┌─────────────────────────────────────┐
│     Vector Database MCP Service     │
├─────────────────────────────────────┤
│  ChromaDB (Local Vector Database)   │
│  Sentence Transformers (Embeddings) │
│  FastMCP Server (Port 8018)         │
└─────────────────────────────────────┘
         ↕ MCP Protocol
┌─────────────────────────────────────┐
│    Master MCP Orchestrator          │
│    Other MCP Services               │
└─────────────────────────────────────┘
```

## Tools Available

### Collection Management
- `vector.collection.create` - Create a new collection
- `vector.collection.list` - List all collections
- `vector.collection.info` - Get collection details

### Document Operations
- `vector.document.add` - Add documents with automatic embedding
- `vector.document.update` - Update existing documents
- `vector.document.delete` - Delete documents

### Search Operations
- `vector.search.semantic` - Semantic search within a collection
- `vector.search.cross_service` - Search across multiple service collections

### Service Integration
- `vector.index.service` - Index data from other MCP services

## Usage Examples

### 1. Basic Document Storage and Search

```python
# Add documents
await vector.document.add(
    documents=[
        "The quick brown fox jumps over the lazy dog",
        "Machine learning models require training data",
        "Docker containers provide isolated environments"
    ],
    metadatas=[
        {"type": "example", "category": "animals"},
        {"type": "tech", "category": "ml"},
        {"type": "tech", "category": "devops"}
    ]
)

# Semantic search
results = await vector.search.semantic(
    query="artificial intelligence training",
    n_results=5
)
```

### 2. Cross-Service Integration

```python
# Index documentation from docs service
await vector.index.service(
    service="docs",
    data_type="documentation",
    documents=[
        {"id": "1", "title": "Setup Guide", "content": "..."},
        {"id": "2", "title": "API Reference", "content": "..."}
    ]
)

# Search across services
results = await vector.search.cross_service(
    query="how to configure authentication",
    services=["docs", "cmdb"]
)
```

### 3. Creating Domain-Specific Collections

```python
# Create a trading knowledge collection
await vector.collection.create(
    name="trading_strategies",
    description="Cryptocurrency trading strategies and analysis",
    metadata={"domain": "crypto", "version": "1.0"}
)

# Add trading documents
await vector.document.add(
    collection="trading_strategies",
    documents=[
        "RSI below 30 indicates oversold conditions...",
        "MACD crossover signals potential trend reversal..."
    ]
)
```

## Configuration

Environment variables:
- `MCP_PORT` - Service port (default: 8018)
- `CHROMA_PERSIST_DIR` - ChromaDB data directory (default: /app/data/chroma)
- `EMBEDDING_MODEL` - Sentence Transformer model (default: all-MiniLM-L6-v2)
- `DEFAULT_COLLECTION` - Default collection name (default: mcp_knowledge)

## Integration with Other Services

### Documentation Service Enhancement
```python
# In 11_documentation_mcp, after creating a document:
await vector.index.service(
    service="docs",
    data_type="documentation",
    documents=[{
        "id": doc_id,
        "title": title,
        "content": content,
        "path": file_path,
        "tags": tags
    }]
)
```

### CMDB Semantic Search
```python
# Index CMDB entries for semantic search
await vector.index.service(
    service="cmdb",
    data_type="assets",
    documents=[{
        "id": asset_id,
        "hostname": hostname,
        "description": f"{hostname} {services} {os_type}",
        "metadata": {...}
    }]
)
```

### Crypto Trading Context
```python
# Store market analysis for context
await vector.document.add(
    collection="market_analysis",
    documents=[analysis_text],
    metadatas=[{
        "timestamp": timestamp,
        "symbol": "BTC/USDT",
        "indicators": ["RSI", "MACD"],
        "sentiment": "bullish"
    }]
)
```

## Performance Considerations

- **Embedding Model**: all-MiniLM-L6-v2 provides good balance of speed and quality
- **Batch Operations**: Add multiple documents in one call for efficiency
- **Collection Size**: ChromaDB handles millions of vectors efficiently
- **Search Speed**: Sub-second search for collections under 1M documents

## Security Notes

- No external API calls - all processing is local
- Data persisted in Docker volume
- No sensitive data leaves the container
- Supports metadata filtering for access control

## Future Enhancements

1. **Multi-Modal Embeddings**: Support for images and structured data
2. **Hybrid Search**: Combine semantic and keyword search
3. **Fine-Tuned Models**: Domain-specific embedding models
4. **Clustering**: Automatic document clustering and categorization
5. **Knowledge Graphs**: Build relationships between documents
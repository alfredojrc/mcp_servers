#!/usr/bin/env python3
"""
Vector Database MCP Service

Provides semantic search and embedding capabilities using ChromaDB and local embeddings.
No external API keys required - uses Sentence Transformers for embeddings.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import uuid

from fastmcp import FastMCP
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Configuration
MCP_PORT = int(os.getenv("MCP_PORT", 8018))
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "/app/data/chroma")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
DEFAULT_COLLECTION = os.getenv("DEFAULT_COLLECTION", "mcp_knowledge")

# Initialize FastMCP
mcp = FastMCP(
    name="Vector Database MCP Service",
    instructions="""
    Vector database service for semantic search and embeddings.
    Uses ChromaDB with local Sentence Transformer embeddings.
    
    Key features:
    - Create and manage collections
    - Add documents with metadata
    - Semantic search with similarity scores
    - Query by vector similarity
    - No external API dependencies
    """
)

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(
    path=CHROMA_PERSIST_DIR,
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)

# Initialize embedding model
embedding_model = SentenceTransformer(EMBEDDING_MODEL)
logger.info(f"Loaded embedding model: {EMBEDDING_MODEL}")

# Ensure default collection exists
try:
    default_collection = chroma_client.get_or_create_collection(
        name=DEFAULT_COLLECTION,
        metadata={"description": "Default MCP knowledge collection"}
    )
    logger.info(f"Default collection '{DEFAULT_COLLECTION}' ready")
except Exception as e:
    logger.error(f"Failed to create default collection: {e}")

@mcp.tool("vector.collection.create")
async def create_collection(
    name: str,
    description: str = "",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a new vector collection."""
    try:
        collection = chroma_client.create_collection(
            name=name,
            metadata={
                "description": description,
                "created_at": datetime.now().isoformat(),
                **(metadata or {})
            }
        )
        return {
            "success": True,
            "collection": name,
            "message": f"Collection '{name}' created successfully"
        }
    except Exception as e:
        if "already exists" in str(e):
            return {
                "success": False,
                "error": f"Collection '{name}' already exists"
            }
        return {"success": False, "error": str(e)}

@mcp.tool("vector.collection.list")
async def list_collections() -> Dict[str, Any]:
    """List all vector collections."""
    try:
        collections = chroma_client.list_collections()
        return {
            "success": True,
            "collections": [
                {
                    "name": col.name,
                    "metadata": col.metadata,
                    "count": col.count()
                }
                for col in collections
            ]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool("vector.document.add")
async def add_documents(
    collection: str = DEFAULT_COLLECTION,
    documents: List[str] = None,
    metadatas: Optional[List[Dict[str, Any]]] = None,
    ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Add documents to a collection with automatic embedding generation."""
    try:
        col = chroma_client.get_collection(collection)
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        # Generate embeddings
        embeddings = embedding_model.encode(documents).tolist()
        
        # Add to collection
        col.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas or [{} for _ in documents],
            ids=ids
        )
        
        return {
            "success": True,
            "count": len(documents),
            "collection": collection,
            "message": f"Added {len(documents)} documents to '{collection}'"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool("vector.search.semantic")
async def semantic_search(
    query: str,
    collection: str = DEFAULT_COLLECTION,
    n_results: int = 10,
    where: Optional[Dict[str, Any]] = None,
    include_distance: bool = True
) -> Dict[str, Any]:
    """Perform semantic search in a collection."""
    try:
        col = chroma_client.get_collection(collection)
        
        # Generate query embedding
        query_embedding = embedding_model.encode([query])[0].tolist()
        
        # Search
        results = col.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            result = {
                "id": results['ids'][0][i],
                "document": results['documents'][0][i],
                "metadata": results['metadatas'][0][i]
            }
            if include_distance:
                # Convert distance to similarity score (1 - normalized distance)
                distance = results['distances'][0][i]
                result["similarity_score"] = 1 - (distance / 2)  # Normalize for cosine distance
            formatted_results.append(result)
        
        return {
            "success": True,
            "query": query,
            "collection": collection,
            "results": formatted_results,
            "count": len(formatted_results)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool("vector.document.update")
async def update_document(
    document_id: str,
    document: str,
    metadata: Optional[Dict[str, Any]] = None,
    collection: str = DEFAULT_COLLECTION
) -> Dict[str, Any]:
    """Update a document in the collection."""
    try:
        col = chroma_client.get_collection(collection)
        
        # Generate new embedding
        embedding = embedding_model.encode([document])[0].tolist()
        
        # Update document
        col.update(
            ids=[document_id],
            documents=[document],
            embeddings=[embedding],
            metadatas=[metadata] if metadata else None
        )
        
        return {
            "success": True,
            "id": document_id,
            "collection": collection,
            "message": f"Document '{document_id}' updated successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool("vector.document.delete")
async def delete_documents(
    ids: List[str],
    collection: str = DEFAULT_COLLECTION
) -> Dict[str, Any]:
    """Delete documents from a collection."""
    try:
        col = chroma_client.get_collection(collection)
        col.delete(ids=ids)
        
        return {
            "success": True,
            "count": len(ids),
            "collection": collection,
            "message": f"Deleted {len(ids)} documents from '{collection}'"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool("vector.collection.info")
async def get_collection_info(collection: str = DEFAULT_COLLECTION) -> Dict[str, Any]:
    """Get detailed information about a collection."""
    try:
        col = chroma_client.get_collection(collection)
        
        return {
            "success": True,
            "collection": collection,
            "count": col.count(),
            "metadata": col.metadata,
            "embedding_dimension": 384  # For all-MiniLM-L6-v2
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool("vector.index.service")
async def index_service_data(
    service: str,
    data_type: str,
    documents: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Index data from other MCP services for cross-service search."""
    try:
        # Create service-specific collection if needed
        collection_name = f"{service}_{data_type}"
        try:
            col = chroma_client.create_collection(
                name=collection_name,
                metadata={
                    "service": service,
                    "data_type": data_type,
                    "indexed_at": datetime.now().isoformat()
                }
            )
        except:
            col = chroma_client.get_collection(collection_name)
        
        # Prepare documents for indexing
        texts = []
        metadatas = []
        ids = []
        
        for doc in documents:
            # Create searchable text from document
            text_parts = []
            if "title" in doc:
                text_parts.append(f"Title: {doc['title']}")
            if "content" in doc:
                text_parts.append(f"Content: {doc['content']}")
            if "description" in doc:
                text_parts.append(f"Description: {doc['description']}")
            
            # Add other fields to text for better search
            for key, value in doc.items():
                if key not in ["id", "title", "content", "description"] and isinstance(value, str):
                    text_parts.append(f"{key}: {value}")
            
            text = "\n".join(text_parts)
            texts.append(text)
            
            # Prepare metadata
            metadata = {
                "service": service,
                "data_type": data_type,
                "indexed_at": datetime.now().isoformat(),
                **{k: v for k, v in doc.items() if k != "content"}
            }
            metadatas.append(metadata)
            
            # Generate ID
            doc_id = doc.get("id", str(uuid.uuid4()))
            ids.append(f"{service}_{data_type}_{doc_id}")
        
        # Generate embeddings and add to collection
        embeddings = embedding_model.encode(texts).tolist()
        col.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        return {
            "success": True,
            "service": service,
            "data_type": data_type,
            "count": len(documents),
            "collection": collection_name,
            "message": f"Indexed {len(documents)} {data_type} documents from {service}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool("vector.search.cross_service")
async def cross_service_search(
    query: str,
    services: Optional[List[str]] = None,
    n_results: int = 10
) -> Dict[str, Any]:
    """Search across multiple service collections."""
    try:
        all_results = []
        collections_searched = []
        
        # Get all collections
        all_collections = chroma_client.list_collections()
        
        for col in all_collections:
            # Filter by services if specified
            if services:
                service_match = False
                for service in services:
                    if col.name.startswith(f"{service}_"):
                        service_match = True
                        break
                if not service_match:
                    continue
            
            # Skip default collection unless no services specified
            if col.name == DEFAULT_COLLECTION and services:
                continue
            
            collections_searched.append(col.name)
            
            # Search in this collection
            query_embedding = embedding_model.encode([query])[0].tolist()
            results = col.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            # Add results with collection info
            for i in range(len(results['ids'][0])):
                all_results.append({
                    "collection": col.name,
                    "id": results['ids'][0][i],
                    "document": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "similarity_score": 1 - (results['distances'][0][i] / 2)
                })
        
        # Sort by similarity score
        all_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Limit to n_results
        all_results = all_results[:n_results]
        
        return {
            "success": True,
            "query": query,
            "collections_searched": collections_searched,
            "results": all_results,
            "count": len(all_results)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# Health check endpoint
@mcp.resource("vector://health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check ChromaDB connection
        collections = chroma_client.list_collections()
        return {
            "status": "healthy",
            "service": "Vector Database MCP",
            "chroma_status": "connected",
            "collections_count": len(collections),
            "embedding_model": EMBEDDING_MODEL,
            "persist_directory": CHROMA_PERSIST_DIR
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    app = mcp.sse_app()
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT, log_level="info")
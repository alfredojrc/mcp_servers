#!/usr/bin/env python3
"""
Minimal Vector Database MCP Service

Uses lightweight in-memory vector storage for semantic search.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import uuid
import hashlib

from fastmcp import FastMCP
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Configuration
MCP_PORT = int(os.getenv("MCP_PORT", 8018))
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize FastMCP
mcp = FastMCP(
    name="Vector Database MCP Service",
    instructions="""
    Minimal vector database service for semantic search.
    Uses TF-IDF vectors for text similarity without heavy dependencies.
    
    Key features:
    - Create and manage collections
    - Add documents with metadata
    - Semantic search with similarity scores
    - Persistent storage
    - No external API dependencies
    """
)

class VectorCollection:
    def __init__(self, name: str, metadata: Dict = None):
        self.name = name
        self.metadata = metadata or {}
        self.documents = []
        self.metadatas = []
        self.ids = []
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.vectors = None
        
    def add(self, documents: List[str], metadatas: List[Dict], ids: List[str]):
        """Add documents to collection"""
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)
        self.ids.extend(ids)
        
        # Refit vectorizer with all documents
        if self.documents:
            self.vectors = self.vectorizer.fit_transform(self.documents)
    
    def search(self, query: str, n_results: int = 10):
        """Search for similar documents"""
        if not self.documents:
            return []
        
        # Transform query
        query_vec = self.vectorizer.transform([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vec, self.vectors)[0]
        
        # Get top results
        top_indices = np.argsort(similarities)[::-1][:n_results]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # Only return results with some similarity
                results.append({
                    "id": self.ids[idx],
                    "document": self.documents[idx],
                    "metadata": self.metadatas[idx],
                    "similarity_score": float(similarities[idx])
                })
        
        return results
    
    def delete(self, ids: List[str]):
        """Delete documents by ID"""
        indices_to_keep = [i for i, doc_id in enumerate(self.ids) if doc_id not in ids]
        
        self.documents = [self.documents[i] for i in indices_to_keep]
        self.metadatas = [self.metadatas[i] for i in indices_to_keep]
        self.ids = [self.ids[i] for i in indices_to_keep]
        
        # Refit vectorizer
        if self.documents:
            self.vectors = self.vectorizer.fit_transform(self.documents)
        else:
            self.vectors = None
    
    def save(self):
        """Save collection to disk"""
        filepath = os.path.join(DATA_DIR, f"{self.name}.pkl")
        with open(filepath, 'wb') as f:
            pickle.dump({
                'name': self.name,
                'metadata': self.metadata,
                'documents': self.documents,
                'metadatas': self.metadatas,
                'ids': self.ids,
                'vectorizer': self.vectorizer,
                'vectors': self.vectors
            }, f)
    
    @classmethod
    def load(cls, name: str):
        """Load collection from disk"""
        filepath = os.path.join(DATA_DIR, f"{name}.pkl")
        if not os.path.exists(filepath):
            return None
            
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        collection = cls(data['name'], data['metadata'])
        collection.documents = data['documents']
        collection.metadatas = data['metadatas']
        collection.ids = data['ids']
        collection.vectorizer = data['vectorizer']
        collection.vectors = data['vectors']
        
        return collection

# In-memory collection storage
collections = {}

# Load existing collections on startup
for filename in os.listdir(DATA_DIR):
    if filename.endswith('.pkl'):
        name = filename[:-4]
        try:
            collection = VectorCollection.load(name)
            if collection:
                collections[name] = collection
                logger.info(f"Loaded collection: {name}")
        except Exception as e:
            logger.error(f"Failed to load collection {name}: {e}")

# Ensure default collection exists
if "mcp_knowledge" not in collections:
    collections["mcp_knowledge"] = VectorCollection(
        "mcp_knowledge",
        {"description": "Default MCP knowledge collection"}
    )
    collections["mcp_knowledge"].save()

@mcp.tool("vector.collection.create")
async def create_collection(
    name: str,
    description: str = "",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a new vector collection."""
    try:
        if name in collections:
            return {
                "success": False,
                "error": f"Collection '{name}' already exists"
            }
        
        collection = VectorCollection(
            name,
            {
                "description": description,
                "created_at": datetime.now().isoformat(),
                **(metadata or {})
            }
        )
        collections[name] = collection
        collection.save()
        
        return {
            "success": True,
            "collection": name,
            "message": f"Collection '{name}' created successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool("vector.collection.list")
async def list_collections() -> Dict[str, Any]:
    """List all vector collections."""
    try:
        return {
            "success": True,
            "collections": [
                {
                    "name": name,
                    "metadata": col.metadata,
                    "count": len(col.documents)
                }
                for name, col in collections.items()
            ]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool("vector.document.add")
async def add_documents(
    collection: str = "mcp_knowledge",
    documents: List[str] = None,
    metadatas: Optional[List[Dict[str, Any]]] = None,
    ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Add documents to a collection."""
    try:
        if collection not in collections:
            return {"success": False, "error": f"Collection '{collection}' not found"}
        
        col = collections[collection]
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        # Add to collection
        col.add(
            documents=documents,
            metadatas=metadatas or [{} for _ in documents],
            ids=ids
        )
        
        # Save to disk
        col.save()
        
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
    collection: str = "mcp_knowledge",
    n_results: int = 10,
    where: Optional[Dict[str, Any]] = None,
    include_distance: bool = True
) -> Dict[str, Any]:
    """Perform semantic search in a collection."""
    try:
        if collection not in collections:
            return {"success": False, "error": f"Collection '{collection}' not found"}
        
        col = collections[collection]
        
        # Search
        results = col.search(query, n_results)
        
        # Apply metadata filters if provided
        if where:
            filtered_results = []
            for result in results:
                match = True
                for key, value in where.items():
                    if result["metadata"].get(key) != value:
                        match = False
                        break
                if match:
                    filtered_results.append(result)
            results = filtered_results
        
        return {
            "success": True,
            "query": query,
            "collection": collection,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool("vector.document.delete")
async def delete_documents(
    ids: List[str],
    collection: str = "mcp_knowledge"
) -> Dict[str, Any]:
    """Delete documents from a collection."""
    try:
        if collection not in collections:
            return {"success": False, "error": f"Collection '{collection}' not found"}
        
        col = collections[collection]
        col.delete(ids)
        col.save()
        
        return {
            "success": True,
            "count": len(ids),
            "collection": collection,
            "message": f"Deleted {len(ids)} documents from '{collection}'"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool("vector.collection.info")
async def get_collection_info(collection: str = "mcp_knowledge") -> Dict[str, Any]:
    """Get detailed information about a collection."""
    try:
        if collection not in collections:
            return {"success": False, "error": f"Collection '{collection}' not found"}
        
        col = collections[collection]
        
        return {
            "success": True,
            "collection": collection,
            "count": len(col.documents),
            "metadata": col.metadata,
            "features": col.vectorizer.max_features if hasattr(col.vectorizer, 'max_features') else "N/A"
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
        
        if collection_name not in collections:
            await create_collection(
                name=collection_name,
                description=f"Data from {service} service",
                metadata={
                    "service": service,
                    "data_type": data_type,
                    "indexed_at": datetime.now().isoformat()
                }
            )
        
        # Prepare documents for indexing
        texts = []
        metadatas = []
        ids = []
        
        for doc in documents:
            # Create searchable text from document
            text_parts = []
            for key, value in doc.items():
                if isinstance(value, str):
                    text_parts.append(f"{key}: {value}")
            
            text = "\n".join(text_parts)
            texts.append(text)
            
            # Prepare metadata
            metadata = {
                "service": service,
                "data_type": data_type,
                "indexed_at": datetime.now().isoformat(),
                **doc
            }
            metadatas.append(metadata)
            
            # Generate ID
            doc_id = doc.get("id", str(uuid.uuid4()))
            ids.append(f"{service}_{data_type}_{doc_id}")
        
        # Add to collection
        await add_documents(
            collection=collection_name,
            documents=texts,
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

# Health check endpoint
@mcp.resource("vector://health")
async def health_check():
    """Health check endpoint."""
    try:
        return {
            "status": "healthy",
            "service": "Vector Database MCP (Minimal)",
            "collections_count": len(collections),
            "data_directory": DATA_DIR
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
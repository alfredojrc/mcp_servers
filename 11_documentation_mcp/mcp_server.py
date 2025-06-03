import os
import logging
from typing import Optional, List, Dict, Any
import json
from datetime import datetime as dt
from pathlib import Path
import hashlib
import difflib
import frontmatter
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, DATETIME, KEYWORD
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.query import And, Or, Term

from mcp.server.fastmcp import FastMCP

# JSON Formatter Class
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
        return json.dumps(log_entry)

# Logging Setup
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

SERVICE_NAME = "documentation-service"
json_formatter = JSONFormatter(SERVICE_NAME)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(json_formatter)
root_logger.addHandler(stream_handler)
root_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)

# Configuration
MCP_PORT = int(os.getenv("MCP_PORT", 8011))
DOCS_ROOT = Path(os.getenv("DOCS_ROOT", "/workspace/docs"))
REQUIRE_APPROVAL = os.getenv("REQUIRE_APPROVAL", "true").lower() == "true"
INDEX_PATH = Path("/workspace/search_index")

# Ensure directories exist
DOCS_ROOT.mkdir(parents=True, exist_ok=True)
INDEX_PATH.mkdir(parents=True, exist_ok=True)

# Categories
CATEGORIES = [
    "projects",
    "services", 
    "whitepapers",
    "guides",
    "api",
    "knowledge"
]

# Initialize search index
schema = Schema(
    id=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    content=TEXT(stored=True),
    category=KEYWORD(stored=True),
    tags=KEYWORD(stored=True, commas=True),
    created=DATETIME(stored=True),
    modified=DATETIME(stored=True),
    author=TEXT(stored=True),
    path=TEXT(stored=True)
)

# Create or open index
if not INDEX_PATH.exists() or not index.exists_in(str(INDEX_PATH)):
    ix = index.create_in(str(INDEX_PATH), schema)
else:
    ix = index.open_dir(str(INDEX_PATH))

# Metrics
metrics = {
    "searches_performed": 0,
    "documents_accessed": 0,
    "documents_created": 0,
    "documents_updated": 0,
    "popular_documents": {},
    "search_queries": []
}

# Initialize FastMCP
mcp = FastMCP("Documentation MCP Server")

def generate_doc_id(title: str, category: str) -> str:
    """Generate unique document ID"""
    content = f"{category}:{title}:{dt.now().isoformat()}"
    return hashlib.md5(content.encode()).hexdigest()[:12]

def index_document(doc_data: Dict[str, Any]):
    """Add or update document in search index"""
    writer = ix.writer()
    writer.update_document(
        id=doc_data["id"],
        title=doc_data["title"],
        content=doc_data["content"],
        category=doc_data["category"],
        tags=",".join(doc_data.get("tags", [])),
        created=dt.fromisoformat(doc_data["created"]),
        modified=dt.fromisoformat(doc_data["modified"]),
        author=doc_data.get("author", ""),
        path=doc_data["path"]
    )
    writer.commit()

def load_document(file_path: Path) -> Dict[str, Any]:
    """Load document with frontmatter"""
    try:
        post = frontmatter.load(file_path)
        return {
            "id": post.metadata.get("id"),
            "title": post.metadata.get("title"),
            "content": post.content,
            "category": post.metadata.get("category"),
            "tags": post.metadata.get("tags", []),
            "created": post.metadata.get("created"),
            "modified": post.metadata.get("modified"),
            "author": post.metadata.get("author"),
            "version": post.metadata.get("version", "1.0"),
            "path": str(file_path.relative_to(DOCS_ROOT))
        }
    except Exception as e:
        logger.error(f"Error loading document {file_path}: {e}")
        return None

@mcp.tool("docs.search")
async def search_docs(
    query: str,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Search documentation by keyword, category, or tags.
    
    Args:
        query: Search query string
        category: Optional category filter
        tags: Optional list of tags to filter by
        
    Returns:
        List of matching documents with snippets
    """
    metrics["searches_performed"] += 1
    metrics["search_queries"].append(query)
    
    try:
        with ix.searcher() as searcher:
            # Build query
            parser = MultifieldParser(["title", "content"], schema=ix.schema)
            q = parser.parse(query)
            
            # Add filters
            if category:
                q = And([q, Term("category", category)])
            
            if tags:
                tag_queries = [Term("tags", tag) for tag in tags]
                q = And([q, Or(tag_queries)])
            
            # Execute search
            results = searcher.search(q, limit=20)
            
            # Format results
            documents = []
            for hit in results:
                doc = {
                    "id": hit["id"],
                    "title": hit["title"],
                    "category": hit["category"],
                    "snippet": hit.highlights("content", top=3) or hit["content"][:200] + "...",
                    "score": hit.score,
                    "path": hit["path"]
                }
                documents.append(doc)
            
            logger.info(f"Search for '{query}' returned {len(documents)} results")
            
            return {
                "query": query,
                "count": len(documents),
                "documents": documents
            }
            
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return {"error": str(e), "documents": []}

@mcp.tool("docs.get")
async def get_document(
    doc_id: str,
    version: str = "latest"
) -> Dict[str, Any]:
    """
    Retrieve a specific document by ID.
    
    Args:
        doc_id: Document ID
        version: Version to retrieve (default: latest)
        
    Returns:
        Complete document content and metadata
    """
    metrics["documents_accessed"] += 1
    metrics["popular_documents"][doc_id] = metrics["popular_documents"].get(doc_id, 0) + 1
    
    try:
        # Search for document by ID
        with ix.searcher() as searcher:
            results = searcher.search(Term("id", doc_id))
            
            if not results:
                return {"error": f"Document {doc_id} not found"}
            
            hit = results[0]
            doc_path = DOCS_ROOT / hit["path"]
            
            if not doc_path.exists():
                return {"error": f"Document file not found: {hit['path']}"}
            
            # Load full document
            doc = load_document(doc_path)
            if doc:
                logger.info(f"Retrieved document: {doc_id}")
                return doc
            else:
                return {"error": "Failed to load document"}
                
    except Exception as e:
        logger.error(f"Error retrieving document {doc_id}: {str(e)}")
        return {"error": str(e)}

@mcp.tool("docs.list")
async def list_documents(
    category: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    List all documents or filter by category.
    
    Args:
        category: Optional category filter
        limit: Maximum number of documents to return
        
    Returns:
        List of document summaries
    """
    try:
        documents = []
        
        # Determine search path
        search_path = DOCS_ROOT
        if category and category in CATEGORIES:
            search_path = DOCS_ROOT / category
        
        # Find all markdown files
        for doc_file in search_path.rglob("*.md"):
            if len(documents) >= limit:
                break
                
            doc = load_document(doc_file)
            if doc:
                # Create summary
                summary = {
                    "id": doc["id"],
                    "title": doc["title"],
                    "category": doc["category"],
                    "tags": doc["tags"],
                    "created": doc["created"],
                    "modified": doc["modified"],
                    "author": doc["author"]
                }
                documents.append(summary)
        
        return {
            "count": len(documents),
            "category": category,
            "documents": documents
        }
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        return {"error": str(e), "documents": []}

@mcp.tool("docs.create")
async def create_document(
    title: str,
    content: str,
    category: str,
    tags: List[str],
    metadata: Optional[Dict[str, Any]] = None,
    approval_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new document (requires approval).
    
    Args:
        title: Document title
        content: Document content (Markdown)
        category: Document category
        tags: List of tags
        metadata: Additional metadata
        approval_token: Approval token for creating document
        
    Returns:
        Created document information
    """
    if REQUIRE_APPROVAL and not approval_token:
        return {"error": "Document creation requires approval token"}
    
    if category not in CATEGORIES:
        return {"error": f"Invalid category. Must be one of: {', '.join(CATEGORIES)}"}
    
    try:
        # Generate document ID
        doc_id = generate_doc_id(title, category)
        
        # Create document metadata
        doc_metadata = {
            "id": doc_id,
            "title": title,
            "category": category,
            "tags": tags,
            "created": dt.now().isoformat(),
            "modified": dt.now().isoformat(),
            "author": metadata.get("author", "system") if metadata else "system",
            "version": "1.0"
        }
        
        # Add custom metadata
        if metadata:
            doc_metadata.update(metadata)
        
        # Create document with frontmatter
        post = frontmatter.Post(content, **doc_metadata)
        
        # Determine file path
        category_dir = DOCS_ROOT / category
        category_dir.mkdir(exist_ok=True)
        
        filename = f"{doc_id}_{title.lower().replace(' ', '_')}.md"
        file_path = category_dir / filename
        
        # Save document
        with open(file_path, 'w') as f:
            f.write(frontmatter.dumps(post))
        
        # Index document
        doc_data = load_document(file_path)
        index_document(doc_data)
        
        metrics["documents_created"] += 1
        logger.info(f"Created document: {doc_id} - {title}")
        
        return {
            "id": doc_id,
            "title": title,
            "category": category,
            "path": str(file_path.relative_to(DOCS_ROOT)),
            "created": doc_metadata["created"]
        }
        
    except Exception as e:
        logger.error(f"Error creating document: {str(e)}")
        return {"error": str(e)}

@mcp.tool("docs.update")
async def update_document(
    doc_id: str,
    content: str,
    version_note: str,
    approval_token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing document (requires approval).
    
    Args:
        doc_id: Document ID to update
        content: New content
        version_note: Note describing the changes
        approval_token: Approval token
        
    Returns:
        Updated document information
    """
    if REQUIRE_APPROVAL and not approval_token:
        return {"error": "Document update requires approval token"}
    
    try:
        # Find existing document
        existing = await get_document(doc_id)
        if "error" in existing:
            return existing
        
        # Update metadata
        existing["modified"] = dt.now().isoformat()
        existing["version"] = str(float(existing.get("version", "1.0")) + 0.1)
        existing["version_note"] = version_note
        
        # Create updated document
        post = frontmatter.Post(content, **{
            k: v for k, v in existing.items() 
            if k not in ["content", "path"]
        })
        
        # Save updated document
        file_path = DOCS_ROOT / existing["path"]
        with open(file_path, 'w') as f:
            f.write(frontmatter.dumps(post))
        
        # Re-index document
        doc_data = load_document(file_path)
        index_document(doc_data)
        
        metrics["documents_updated"] += 1
        logger.info(f"Updated document: {doc_id} to version {existing['version']}")
        
        return {
            "id": doc_id,
            "version": existing["version"],
            "modified": existing["modified"],
            "version_note": version_note
        }
        
    except Exception as e:
        logger.error(f"Error updating document {doc_id}: {str(e)}")
        return {"error": str(e)}

@mcp.tool("docs.categories.list")
async def list_categories() -> Dict[str, Any]:
    """List all available documentation categories."""
    return {
        "categories": CATEGORIES,
        "count": len(CATEGORIES)
    }

@mcp.tool("docs.tags.list")
async def list_tags() -> Dict[str, Any]:
    """List all available tags."""
    try:
        all_tags = set()
        
        with ix.searcher() as searcher:
            for doc in searcher.documents():
                if doc.get("tags"):
                    tags = doc["tags"].split(",")
                    all_tags.update(tag.strip() for tag in tags if tag.strip())
        
        return {
            "tags": sorted(list(all_tags)),
            "count": len(all_tags)
        }
        
    except Exception as e:
        logger.error(f"Error listing tags: {str(e)}")
        return {"error": str(e), "tags": []}

@mcp.tool("docs.getMetrics")
async def get_metrics() -> Dict[str, Any]:
    """Get documentation service metrics."""
    # Get top 10 popular documents
    top_docs = sorted(
        metrics["popular_documents"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    return {
        "service": SERVICE_NAME,
        "metrics": {
            **metrics,
            "popular_documents": dict(top_docs),
            "recent_searches": metrics["search_queries"][-10:]
        },
        "timestamp": dt.now().isoformat()
    }

# Initialize sample documentation
def initialize_sample_docs():
    """Create sample documentation if none exists"""
    sample_docs = [
        {
            "title": "MCP Architecture Overview",
            "category": "projects",
            "tags": ["architecture", "mcp", "overview"],
            "content": """# MCP Architecture Overview

The Multi-Agent MCP System follows a hub-and-spoke architecture where specialized services communicate through a central orchestrator.

## Key Components

1. **Central Orchestrator (00_master_mcp)**: Routes requests to appropriate services
2. **Specialized Services**: Each service handles specific domains
3. **Shared Network**: All services connect via Docker network

## Design Principles

- Modularity: Each service is independent
- Scalability: Services can be scaled individually
- Security: Least privilege access per service
"""
        },
        {
            "title": "Getting Started with MCP",
            "category": "guides",
            "tags": ["tutorial", "getting-started", "mcp"],
            "content": """# Getting Started with MCP

This guide will help you get started with the MCP system.

## Prerequisites

- Docker and Docker Compose installed
- Basic understanding of microservices
- Python 3.9+

## Quick Start

1. Clone the repository
2. Run `docker-compose up -d`
3. Check service health with `python check_health.py`
4. Start using the services!
"""
        }
    ]
    
    for doc in sample_docs:
        # Check if docs exist
        if any(DOCS_ROOT.rglob("*.md")):
            break
            
        # Create sample doc
        create_doc_sync(
            title=doc["title"],
            content=doc["content"],
            category=doc["category"],
            tags=doc["tags"]
        )

def create_doc_sync(title, content, category, tags):
    """Synchronous version for initialization"""
    import asyncio
    asyncio.run(create_document(
        title=title,
        content=content,
        category=category,
        tags=tags,
        approval_token="init"
    ))

# Initialize on startup
logger.info(f"Documentation MCP Server starting on port {MCP_PORT}")
logger.info(f"Documents root: {DOCS_ROOT}")
logger.info(f"Approval required: {REQUIRE_APPROVAL}")

# Create category directories
for category in CATEGORIES:
    (DOCS_ROOT / category).mkdir(exist_ok=True)

# Initialize sample docs
try:
    initialize_sample_docs()
except Exception as e:
    logger.warning(f"Could not initialize sample docs: {e}")

if __name__ == "__main__":
    # Run the FastMCP server
    import uvicorn
    uvicorn.run(mcp, host="0.0.0.0", port=MCP_PORT, log_level="info")
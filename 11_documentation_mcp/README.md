# 11_documentation_mcp (Port 8011)

## Purpose
Provides centralized documentation management for all projects, services, whitepapers, technical specifications, and knowledge base articles. This service acts as a single source of truth for all documentation across the MCP ecosystem.

Tools are organized under the `docs.*` namespace.

## Namespaced Tools

### Document Management
- **`docs.search(query: str, category: str = None, tags: list[str] = None) -> list[dict]`**: 
  Search documentation by keyword, category, or tags. Returns relevant documents with snippets.

- **`docs.get(doc_id: str, version: str = "latest") -> dict`**: 
  Retrieve a specific document by ID, optionally specifying version.

- **`docs.list(category: str = None, limit: int = 50) -> list[dict]`**: 
  List all documents or filter by category.

### Document Creation/Update
- **`docs.create(title: str, content: str, category: str, tags: list[str], metadata: dict) -> dict`**: 
  Create a new document (requires approval).

- **`docs.update(doc_id: str, content: str, version_note: str) -> dict`**: 
  Update an existing document, creating a new version (requires approval).

### Categories & Organization
- **`docs.categories.list() -> list[str]`**: 
  List all available documentation categories.

- **`docs.tags.list() -> list[str]`**: 
  List all available tags.

### Version Control
- **`docs.versions.list(doc_id: str) -> list[dict]`**: 
  List all versions of a document.

- **`docs.versions.diff(doc_id: str, version1: str, version2: str) -> dict`**: 
  Compare two versions of a document.

## Container Layout
```
11_documentation_mcp/
├── Dockerfile
├── entrypoint.sh
├── requirements.txt
├── mcp_server.py
├── docs/              # Documentation storage
│   ├── projects/      # Project documentation
│   ├── services/      # Service-specific docs
│   ├── whitepapers/   # Technical whitepapers
│   ├── guides/        # How-to guides
│   ├── api/           # API documentation
│   └── knowledge/     # Knowledge base articles
└── README.md
```

## Documentation Categories

1. **Projects**: Overall project documentation, architecture, roadmaps
2. **Services**: Individual MCP service documentation
3. **Whitepapers**: Technical deep-dives, design decisions
4. **Guides**: How-to guides, tutorials, best practices
5. **API**: API references, schemas, examples
6. **Knowledge**: FAQs, troubleshooting, tips & tricks

## Implementation Details
- **Framework:** Python with `mcp`/`fastmcp`
- **Storage:** File-based with Git for version control
- **Search:** Full-text search using Whoosh or similar
- **Format:** Markdown with frontmatter metadata

## Operating Principles
1. **Version Control**: All documents are versioned with Git
2. **Approval Required**: Document creation/updates require approval
3. **Read Access**: All read operations are allowed without approval
4. **Structured Metadata**: Each document has title, category, tags, author, date
5. **Search Indexing**: Documents are indexed for fast full-text search

## Configuration
- `MCP_PORT=8011`
- `DOCS_ROOT=/workspace/docs`
- `REQUIRE_APPROVAL=true`
- `INDEX_UPDATE_INTERVAL=300` (seconds)

## Observability
- **Logging**: JSON structured logs with correlation IDs
- **Metrics**: Search queries, document access patterns, popular docs
- **Health Check**: Verifies document index is accessible

## Claude Code Integration

This service is designed to work seamlessly with Claude Code (claude.ai/code).

### Quick Setup
1. Ensure service is running on `http://192.168.68.100:8011`
2. Add `.mcp.json` to your project:
```json
{
  "mcpServers": {
    "documentation": {
      "url": "http://192.168.68.100:8011/sse",
      "transport": "sse"
    }
  }
}
```
3. Restart Claude Code to load the configuration

### Available Commands
- "Search documentation for [topic]"
- "Show me documentation about [feature]"
- "Create documentation for [component]"
- "Update the [document] with [changes]"

### Integration Testing
Run the validation script:
```bash
python test_claude_integration.py
```

For detailed integration guide, see `CLAUDE_CODE_INTEGRATION.md`
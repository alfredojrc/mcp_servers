# Using Documentation MCP from External Projects

## Overview
Yes! External projects can absolutely connect to the documentation MCP service via Claude Code and manage their documentation. This creates a centralized knowledge base for all your projects.

## How It Works

### 1. Connection via Claude Code
When using Claude Code in any project, you can connect to the documentation MCP service running at `http://localhost:8011` (or your deployed URL).

### 2. Available Operations
External projects can:
- **Create** new documentation (`docs.create`)
- **Update** existing documents (`docs.update`)
- **Search** for documentation (`docs.search`)
- **Retrieve** specific documents (`docs.get`)
- **List** documents by category (`docs.list`)

### 3. Documentation Categories
- `projects` - Overall project documentation
- `api` - API references
- `guides` - How-to guides and tutorials
- `whitepapers` - Technical deep-dives
- `knowledge` - FAQs and tips
- `services` - Service-specific docs

## Example Usage in Claude Code

### Creating Project Documentation
```python
# In your project, via Claude Code
async def document_my_project():
    response = await claude_code.execute_tool(
        "docs.create",
        {
            "title": "MyProject - Overview",
            "content": "# MyProject\n\nProject documentation...",
            "category": "projects",
            "tags": ["myproject", "overview"],
            "metadata": {
                "author": "MyProject Team",
                "version": "1.0.0"
            },
            "approval_token": "your-token"
        }
    )
```

### Updating Documentation
```python
# Update when your project changes
async def update_api_docs():
    response = await claude_code.execute_tool(
        "docs.update",
        {
            "doc_id": "abc123",
            "content": "# Updated API Documentation\n\n...",
            "version_note": "Added new endpoints",
            "approval_token": "your-token"
        }
    )
```

### Searching Across All Projects
```python
# Find documentation across all projects
async def find_authentication_docs():
    response = await claude_code.execute_tool(
        "docs.search",
        {
            "query": "authentication oauth",
            "category": "api"
        }
    )
```

## Integration Patterns

### 1. CI/CD Integration
Your CI/CD pipeline can automatically update documentation:
- On new releases: Create release notes
- On API changes: Update API documentation
- On deployment: Update deployment guides

### 2. Development Workflow
Developers can:
- Document new features as they build them
- Update guides when processes change
- Search for existing solutions across all projects

### 3. Knowledge Management
Teams can:
- Build a searchable knowledge base
- Share best practices across projects
- Maintain up-to-date technical documentation

## Security Considerations

### Approval Tokens
- Documentation creation/updates require approval tokens
- This prevents unauthorized modifications
- Tokens can be managed per project or team

### Read vs Write Access
- All read operations (search, get, list) are open
- Write operations (create, update) require approval
- This encourages knowledge sharing while maintaining quality

## Benefits

1. **Centralized Knowledge**: All project documentation in one searchable location
2. **Version Control**: Track changes and maintain history
3. **Cross-Project Learning**: Discover solutions from other projects
4. **Automated Updates**: CI/CD can keep docs current
5. **Consistent Format**: Markdown with metadata ensures uniformity

## Demo Script

Run the included demo to see how external projects can use the documentation service:

```bash
python demo_external_project.py
```

This demonstrates:
- Creating project documentation
- Creating API references
- Creating deployment guides
- Updating existing documentation
- Searching for documents
- Automated CI/CD documentation

## Best Practices

1. **Use Descriptive Titles**: Make documents easy to find
2. **Tag Appropriately**: Use consistent tags across projects
3. **Include Metadata**: Author, version, dates help track ownership
4. **Regular Updates**: Keep documentation current with code changes
5. **Link Between Docs**: Reference related documentation

## Getting Started

1. Ensure the documentation MCP service is running
2. From your project, use Claude Code to connect
3. Create your first document with `docs.create`
4. Search existing docs with `docs.search`
5. Build your knowledge base!

The documentation service becomes a living knowledge base that grows with your projects, accessible from any project using Claude Code.
# 09_n8n_mcp (Port 8009)

## Purpose
Provides tools for interacting with an n8n instance to manage and trigger workflows.

Tools are organized under the `workflows.n8n.*` namespace.

## Namespaced Tools (Examples)

- **`workflows.n8n.workflows.*`**:
  - `listWorkflows() -> list[dict]`: Lists available workflows.
  - `getWorkflow(id: str) -> dict`: Gets details of a specific workflow.
  - `activateWorkflow(id: str)`: Activates a workflow (requires approval).
  - `deactivateWorkflow(id: str)`: Deactivates a workflow (requires approval).
- **`workflows.n8n.executions.*`**:
  - `triggerWorkflow(id: str, data: dict | None = None) -> dict`: Triggers a workflow manually via webhook node (requires approval).
  - `listExecutions(workflowId: str | None = None, limit: int = 50) -> list[dict]`: Lists past executions.
  - `getExecution(id: str) -> dict`: Gets details of a specific execution.

## Container Layout
```
09_n8n_mcp/
├── Dockerfile
├── entrypoint.sh
├── requirements.txt     # Python MCP SDK, requests
├── mcp_server.py
└── README.md
```

## Implementation Details
- **Framework:** Python with `mcp`/`fastmcp` and `requests`.
- **Interaction:** Uses the n8n REST API.

## Operating Principles & Security Considerations
Interacts with an automation platform.

1.  **OS Discovery:** N/A.
2.  **Backup:** Workflow backups should be handled within n8n or via Git integration.
3.  **Approval for Modifications:** Required for activating/deactivating workflows and triggering them (`activateWorkflow`, `deactivateWorkflow`, `triggerWorkflow`).
4.  **Read-Only Allowed:** Listing workflows/executions, getting details is permitted.
5.  **Logging:** Log all API calls, parameters, and responses/errors using structured logging.
6.  **Shell Consistency:** N/A.
7.  **Sensitive File Access:** N/A.
8.  **Interactive Commands:** N/A.
9.  **Critical Actions:** Triggering workflows that perform critical actions downstream require careful consideration and approval.

**Additional Security:**
- **API Key Security:** Store the n8n API key securely using Docker secrets.
- **Network Security:** Ensure the n8n API endpoint is appropriately secured.

## Configuration
- `MCP_PORT=8009`
- `N8N_API_URL` (URL of the n8n instance API)
- `N8N_API_KEY_SECRET_PATH` (Path to mounted Docker secret for API key)

## Observability
- **Logging:** Adheres to project JSON standard, includes `correlation_id`.
- **Metrics:** Implement `workflows.n8n.getMetrics()`.

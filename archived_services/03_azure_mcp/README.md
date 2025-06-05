# 03_azure_mcp (Port 8003)

## Purpose
Provides tools for interacting with Microsoft Azure services using the Azure SDK or APIs.

Tools are organized under the `cloud.azure.*` namespace.

## Namespaced Tools (Examples)

- **`cloud.azure.compute.*`**:
  - `listVMs(resourceGroup: str | None = None) -> list[dict]`
  - `getVMInfo(vmName: str, resourceGroup: str) -> dict`
  - `startVM(vmName: str, resourceGroup: str)` (Requires approval)
  - `stopVM(vmName: str, resourceGroup: str)` (Requires approval)
  - `restartVM(vmName: str, resourceGroup: str)` (Requires approval)
  - `createVM(...)` (Complex - Requires approval)
  - `deleteVM(vmName: str, resourceGroup: str)` (Requires approval)
- **`cloud.azure.storage.*`**:
  - `listStorageAccounts(resourceGroup: str | None = None) -> list[dict]`
  - `listBlobContainers(accountName: str, resourceGroup: str) -> list[str]`
  - `listBlobs(accountName: str, containerName: str, prefix: str | None = None) -> list[str]`
  - `downloadBlob(accountName: str, containerName: str, blobName: str, destinationPath: str)`
  - `uploadBlob(accountName: str, containerName: str, sourcePath: str, destinationBlobName: str)` (Requires approval)
  - `deleteBlob(accountName: str, containerName: str, blobName: str)` (Requires approval)
- **`cloud.azure.sql.*`**:
  - `listSqlServers() -> list[dict]`
  - `listSqlDatabases(serverName: str, resourceGroup: str) -> list[dict]`
  - `restartSqlServer(serverName: str, resourceGroup: str)` (Requires approval)

## Container Layout
```
03_azure_mcp/
├── Dockerfile
├── entrypoint.sh
├── requirements.txt     # Python MCP SDK, azure-mgmt-compute, azure-mgmt-storage, azure-identity, etc.
├── mcp_server.py
└── README.md
```

## Implementation Details
- **Framework:** Python with `mcp`/`fastmcp`.
- **Backend:** Uses the official Azure SDK for Python libraries (e.g., `azure-mgmt-compute`, `azure-mgmt-storage`, `azure-mgmt-sql`).
- **Authentication:** Typically uses `azure-identity` which supports various methods (Environment Variables, Managed Identity, Service Principal, CLI credentials).

## Operating Principles & Security Considerations
Interacts with cloud infrastructure.

1.  **OS Discovery:** N/A (Applies to Azure VMs, not this server).
2.  **Backup:** Handled by Azure services (snapshots, backups, blob versioning).
3.  **Approval for Modifications:** Required for creating/deleting/starting/stopping/restarting VMs, uploading/deleting blobs, restarting SQL servers.
4.  **Read-Only Allowed:** Listing resources, getting info, downloading blobs.
5.  **Logging:** Log all Azure API calls, parameters, and results/errors using structured logging.
6.  **Shell Consistency:** N/A.
7.  **Sensitive File Access:** Reads credentials if configured via environment or files.
8.  **Interactive Commands:** N/A.
9.  **Critical Actions:** VM/blob/SQL creation/deletion/restarts.

**Additional Security:**
- **Credentials:** Use Managed Identity if running in Azure. Otherwise, securely store Service Principal credentials (client ID, secret, tenant ID) using environment variables sourced from Docker secrets.
- **Azure RBAC:** Assign the least privilege Azure roles necessary for the Service Principal or Managed Identity.

## Configuration
- `MCP_PORT=8003`
- `AZURE_CLIENT_ID` (If using Service Principal)
- `AZURE_TENANT_ID` (If using Service Principal)
- `AZURE_CLIENT_SECRET_SECRET_PATH` (Path to mounted Docker secret for SP secret)
- `AZURE_SUBSCRIPTION_ID`

## Observability
- **Logging:** Adheres to project JSON standard, includes `correlation_id`.
- **Metrics:** Implement `cloud.azure.getMetrics()`.

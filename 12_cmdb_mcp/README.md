# 12_cmdb_mcp (Port 8012)

## Purpose
Provides tools to query and manage configuration data from a local source (CSV/SQLite) and external CMDBs (e.g., ServiceNow).

Tools are organized under the `cmdb.*` namespace (e.g., `cmdb.local.*`, `cmdb.servicenow.*`).

## Namespaced Tools (Examples)

- **`cmdb.local.servers.getServerInfo(hostname: str) -> dict`**
- **`cmdb.local.services.getServiceInfo(serviceName: str) -> dict`**
- **`cmdb.servicenow.ci.getCiDetails(sysId: str) -> dict`**

## Operating Principles & Security Considerations
- Read-only access to external systems is generally safe.
- Modifying CMDB data requires approval.
- Securely handle credentials for external CMDBs.

## Configuration
- `MCP_PORT=8012`
- `LOCAL_CMDB_PATH=/data/cmdb.csv`
- `SERVICENOW_INSTANCE`
- `SERVICENOW_USER`
- `SERVICENOW_PASSWORD_SECRET_PATH`

## Observability
- Adheres to project logging/metrics standards. 
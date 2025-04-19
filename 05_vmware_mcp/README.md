# 05_vmware_mcp (Port 5005)

## Purpose
Provides tools for interacting with VMware vSphere (vCenter or standalone ESXi hosts) using the vSphere API.

Tools are organized under the `infra.vmware.*` namespace.

## Namespaced Tools (Examples)

- **`infra.vmware.vms.*`**:
  - `listVMs(folder: str | None = None) -> list[dict]`
  - `getVMInfo(vmName: str) -> dict`
  - `powerOnVm(vmName: str)` (Requires approval)
  - `powerOffVm(vmName: str)` (Requires approval)
  - `rebootVm(vmName: str)` (Requires approval)
  - `createSnapshot(vmName: str, snapshotName: str, description: str | None = None)` (Requires approval)
  - `revertToSnapshot(vmName: str, snapshotName: str)` (Requires approval)
  - `deleteSnapshot(vmName: str, snapshotName: str)` (Requires approval)
  - `cloneVm(sourceVmName: str, newVmName: str, targetFolder: str)` (Requires approval)
- **`infra.vmware.hosts.*`**:
  - `listHosts(clusterName: str | None = None) -> list[dict]`
  - `getHostInfo(hostName: str) -> dict`
  - `enterMaintenanceMode(hostName: str)` (Requires approval)
  - `exitMaintenanceMode(hostName: str)` (Requires approval)

## Container Layout
```
05_vmware_mcp/
├── Dockerfile
├── entrypoint.sh
├── requirements.txt     # Python MCP SDK, pyvmomi
├── mcp_server.py
└── README.md
```

## Implementation Details
- **Framework:** Python with `mcp`/`fastmcp`.
- **Backend:** Uses the `pyvmomi` library to interact with the vSphere API.

## Operating Principles & Security Considerations
Interacts with virtualization infrastructure.

1.  **OS Discovery:** N/A (Applies to guest OS, not hypervisor itself).
2.  **Backup:** Snapshots are backups, but VM/host configs are managed by vCenter/ESXi. Actions modifying these require care.
3.  **Approval for Modifications:** Required for any action changing VM state (power on/off/reboot), snapshots, cloning, or host state (maintenance mode).
4.  **Read-Only Allowed:** Listing VMs/hosts, getting info.
5.  **Logging:** Log all vSphere API calls, parameters, and results/errors using structured logging.
6.  **Shell Consistency:** N/A.
7.  **Sensitive File Access:** N/A.
8.  **Interactive Commands:** N/A.
9.  **Critical Actions:** Power operations, snapshot management, host maintenance mode are critical.

**Additional Security:**
- **vSphere Credentials:** Store vCenter/ESXi username/password securely using Docker secrets.
- **Network Security:** Ensure connectivity to vCenter/ESXi is secured (HTTPS).
- **vSphere Permissions:** Use a dedicated vSphere user/role with the minimum required privileges for the MCP server's actions.

## Configuration
- `MCP_PORT=5005`
- `VCENTER_HOST`
- `VCENTER_USER`
- `VCENTER_PASSWORD_SECRET_PATH`
- `VCENTER_IGNORE_SSL` (Boolean, for self-signed certs - use with caution)

## Observability
- **Logging:** Adheres to project JSON standard, includes `correlation_id`.
- **Metrics:** Implement `infra.vmware.getMetrics()`.

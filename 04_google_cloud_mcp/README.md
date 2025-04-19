# 04_google_cloud_mcp (Port 5004)

## Purpose
Provides tools for interacting with Google Cloud Platform (GCP) services using the GCP SDK or APIs.

Tools are organized under the `cloud.gcloud.*` namespace.

## Namespaced Tools (Examples)

- **`cloud.gcloud.compute.*`**:
  - `listInstances(zone: str | None = None) -> list[dict]`
  - `getInstanceInfo(instanceName: str, zone: str) -> dict`
  - `startInstance(instanceName: str, zone: str)` (Requires approval)
  - `stopInstance(instanceName: str, zone: str)` (Requires approval)
  - `createInstance(instanceName: str, zone: str, machineType: str, imageProject: str, imageFamily: str)` (Requires approval)
  - `deleteInstance(instanceName: str, zone: str)` (Requires approval)
- **`cloud.gcloud.storage.*`**:
  - `listBuckets() -> list[str]`
  - `listBucketObjects(bucketName: str, prefix: str | None = None) -> list[str]`
  - `downloadObject(bucketName: str, objectName: str, destinationPath: str)`
  - `uploadObject(bucketName: str, sourcePath: str, destinationObjectName: str)` (Requires approval)
  - `deleteObject(bucketName: str, objectName: str)` (Requires approval)
- **`cloud.gcloud.sql.*`**:
  - `listSqlInstances() -> list[dict]`
  - `restartSqlInstance(instanceName: str)` (Requires approval)

## Container Layout
```
04_google_cloud_mcp/
├── Dockerfile
├── entrypoint.sh
├── requirements.txt     # Python MCP SDK, google-cloud-compute, google-cloud-storage, etc.
├── mcp_server.py
└── README.md
```

## Implementation Details
- **Framework:** Python with `mcp`/`fastmcp`.
- **Backend:** Uses the official Google Cloud client libraries for Python (e.g., `google-cloud-compute`, `google-cloud-storage`).
- **Authentication:** Typically relies on Application Default Credentials (ADC) within the container. This usually means mounting a service account key file or running the container in an environment where ADC is automatically configured (like Cloud Run, GKE).

## Operating Principles & Security Considerations
Interacts with cloud infrastructure.

1.  **OS Discovery:** N/A (Applies to GCE instances, not this server).
2.  **Backup:** Handled by GCP services (snapshots, bucket versioning). Manifests/configs should be version controlled.
3.  **Approval for Modifications:** Required for creating/deleting/starting/stopping instances, uploading/deleting objects, restarting SQL instances.
4.  **Read-Only Allowed:** Listing resources, getting info, downloading objects.
5.  **Logging:** Log all GCP API calls, parameters, and results/errors using structured logging.
6.  **Shell Consistency:** N/A.
7.  **Sensitive File Access:** Reads the service account key if mounted.
8.  **Interactive Commands:** N/A.
9.  **Critical Actions:** Instance/object creation/deletion, SQL restarts.

**Additional Security:**
- **Service Account Keys:** Securely manage and mount service account keys (use Docker secrets). Avoid storing keys in the image.
- **IAM Permissions:** Assign the least privilege IAM roles necessary for the service account used by the MCP server.

## Configuration
- `MCP_PORT=5004`
- `GOOGLE_APPLICATION_CREDENTIALS` (Path to the mounted service account key file inside the container, e.g., `/secrets/gcp-key.json`)
- `GCP_PROJECT_ID`

## Observability
- **Logging:** Adheres to project JSON standard, includes `correlation_id`.
- **Metrics:** Implement `cloud.gcloud.getMetrics()`.

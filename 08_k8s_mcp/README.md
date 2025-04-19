# 08_k8s_mcp (Port 8008)

## Purpose
Provides tools for interacting with Kubernetes clusters using `kubectl` or Kubernetes client libraries.

Tools are organized under the `infra.k8s.*` namespace.

Reference implementation: [Flux159/mcp-server-kubernetes](https://github.com/Flux159/mcp-server-kubernetes)

## Namespaced Tools (Examples)

- **`infra.k8s.cluster.*`**:
  - `getContexts() -> list[str]`
  - `getCurrentContext() -> str`
  - `switchContext(contextName: str)` (Requires approval)
- **`infra.k8s.pods.*`**:
  - `listPods(namespace: str | None = None, allNamespaces: bool = False) -> list[dict]`
  - `getPod(name: str, namespace: str) -> dict`
  - `getPodLogs(name: str, namespace: str, tail: int = -1, follow: bool = False) -> str`
  - `deletePod(name: str, namespace: str)` (Requires approval)
- **`infra.k8s.deployments.*`**:
  - `listDeployments(namespace: str | None = None) -> list[dict]`
  - `scaleDeployment(name: str, namespace: str, replicas: int)` (Requires approval)
- **`infra.k8s.helm.*`**:
  - `listReleases(namespace: str | None = None) -> list[dict]`
  - `installChart(name: str, chart: str, namespace: str, values: dict | None = None)` (Requires approval)
  - `upgradeChart(name: str, chart: str, namespace: str, values: dict | None = None)` (Requires approval)
  - `uninstallRelease(name: str, namespace: str)` (Requires approval)
- **`infra.k8s.apply.*`**:
  - `applyManifest(yamlContent: str, namespace: str | None = None)` (Requires approval)

## Container Layout
```
08_k8s_mcp/
├── Dockerfile
├── entrypoint.sh
├── requirements.txt     # Python MCP SDK, kubernetes client
├── mcp_server.py
├── .kube/config         # Mounted volume
└── README.md
```

## Implementation Details
- **Framework:** Python with `mcp`/`fastmcp`.
- **Interaction:** Ideally uses the official `kubernetes` Python client library. Alternatively, can shell out to `kubectl` (less robust).
- **Configuration:** Reads Kubeconfig from the standard location (`~/.kube/config`) inside the container, which should be mounted as a volume from the host.

## Operating Principles & Security Considerations
Interacts with potentially production Kubernetes clusters.

1.  **OS Discovery:** N/A (Applies to K8s API/nodes, not this server).
2.  **Backup:** K8s state is managed by etcd; backups are a cluster-level concern. Manifests should be version controlled.
3.  **Approval for Modifications:** Required for *any* action that modifies cluster state: switching context, deleting pods, scaling, applying manifests, Helm installs/upgrades/uninstalls.
4.  **Read-Only Allowed:** Listing resources (pods, deployments, releases, contexts), getting logs, describing resources.
5.  **Logging:** Log all API calls/`kubectl` commands, parameters, and results/errors using structured logging.
6.  **Shell Consistency:** N/A unless shelling out to `kubectl`.
7.  **Sensitive File Access:** Only reads the mounted Kubeconfig.
8.  **Interactive Commands:** N/A.
9.  **Critical Actions:** Applying manifests, Helm operations, deletions are critical.

**Additional Security:**
- **Kubeconfig Security:** Ensure the host's Kubeconfig file has appropriate permissions. Consider using context-specific Kubeconfigs with least privilege if possible.
- **RBAC:** The permissions granted by the Kubeconfig context determine what the server can do. Use RBAC within Kubernetes to limit the service account or user associated with the Kubeconfig.

## Configuration
- `MCP_PORT=8008`
- `WEBCONTROL_PORT=8008` (Internal port the service listens on)
- `KUBECONFIG=/root/.kube/config` (or path inside container where config is mounted)

## Observability
- **Logging:** Adheres to project JSON standard, includes `correlation_id`.
- **Metrics:** Implement `infra.k8s.getMetrics()`.

## Kubernetes Cluster Management Features

The server now includes the following Kubernetes cluster management features:
- View and manage the Kubernetes context
- List, get, create, and delete pods
- List services and deployments
- Execute commands in containers
- View pod logs
- Apply YAML manifests to the cluster
- Describe Kubernetes resources

## Requirements

- Docker for running the container
- A Kubernetes cluster with kubeconfig set up
- kubectl installed (included in the Docker image)

### Kubernetes Setup

The MCP server requires a working Kubernetes cluster to enable the cluster management features. Here are some options:

1. **Docker Desktop Kubernetes**: Enable Kubernetes in Docker Desktop settings
2. **Minikube**: Install and start a Minikube cluster
3. **Kind**: Create a cluster using Kind (Kubernetes IN Docker)
4. **Remote cluster**: Configure kubectl to connect to a remote cluster

Without a running Kubernetes cluster, the server will still function as a documentation server, but the cluster management features will be disabled.

## Running the Server

### Using Docker Compose

The easiest way to run the server is using Docker Compose:

```bash
cd dockers/mcp_servers
docker-compose up -d k8s-mcp
```

### Building and Running Locally

If you want to run the server locally:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the server:
   ```bash
   python main.py
   ```

## API Endpoints

### Documentation Endpoints
- `/`: Server information and available endpoints
- `/docs`: Kubernetes documentation
- `/api`: Kubernetes API reference
- `/status`: Server status and information
- `/search?q=query`: Search Kubernetes documentation
- `/templates`: List available Kubernetes resource templates
- `/templates/<template_name>?format=yaml|json`: Retrieve a specific template

### Kubernetes Cluster Management Endpoints
- `/cluster`: Get cluster information
- `/cluster/contexts`: List available Kubernetes contexts
- `/cluster/namespaces`: List namespaces
- `/cluster/pods`: List pods (optionally filter by namespace)
- `/cluster/pod/<namespace>/<name>`: Get pod details
- `/cluster/pod/<namespace>/<name>/logs`: Get pod logs
- `/cluster/pod/<namespace>/<name>`: Delete pod (DELETE method)
- `/cluster/pod/<namespace>/<name>/exec`: Execute command in a pod (POST method)
- `/cluster/services`: List services
- `/cluster/deployments`: List deployments
- `/cluster/describe/<kind>/<name>`: Describe a Kubernetes resource
- `/cluster/apply`: Apply YAML manifest (POST method)
- `/cluster/create/pod`: Create a pod (POST method)

## Configuration

The server can be configured using environment variables:

- `WEBCONTROL_PORT`: The port on which the server runs (default: 5001)
- `FLASK_ENV`: The Flask environment (development/production)
- `K8S_API_VERSION`: The Kubernetes API version to use for documentation

## Directory Structure

- `static/docs/`: Contains Kubernetes documentation
- `static/api/`: Contains Kubernetes API references
- `static/templates/`: Contains Kubernetes resource templates
- `logs/`: Contains server logs

## Docker vs. Full VM Considerations

### Docker Container (Current Approach)

**Advantages:**
- Lightweight and resource-efficient
- Easy to deploy and scale
- Simplified dependency management
- Better for CI/CD integration

**Disadvantages:**
- Limited isolation compared to VMs
- Shared kernel with host

### Full VM Approach

**Advantages:**
- Complete isolation from host
- Better security isolation
- Can run different operating systems

**Disadvantages:**
- Higher resource overhead
- Slower startup times
- More complex management

**Recommendation:** For an MCP server that primarily serves documentation and API references, a Docker container is sufficient and more efficient. If the server needs to run Kubernetes components directly or requires full OS isolation for security reasons, a VM might be more appropriate.

## Kubernetes Cluster Connection

The server will attempt to connect to your Kubernetes cluster using:
1. The specified kubeconfig file (if provided)
2. In-cluster configuration (if running inside a Kubernetes pod)
3. Default kubeconfig (~/.kube/config)

If none of these methods work, the Kubernetes cluster management features will be disabled, but documentation will still be available. 
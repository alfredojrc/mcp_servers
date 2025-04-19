# 00_master_mcp (Port 5000)

## Purpose
`00_master_mcp` is the *central orchestrator* of the entire multi‑agent system.  It runs as the **MCP Host** and coordinates all downstream MCP service containers (servers).  
Its responsibilities include:

1. Maintaining secure 1‑to‑1 MCP client connections to each specialised server.
2. Aggregating, sanitising and routing context between the LLM and servers.
3. Enforcing security and consent policies.
4. Orchestrating complex workflows that span multiple services (e.g. *query Azure ⇒ ssh to VM ⇒ run k8s helm upgrade*).
5. Providing a single SSE endpoint (`:5000`) so external tools (e.g. Cursor, Claude Desktop) can attach to **one** host and indirectly reach every internal server.

> **Reference**: MCP host / client / server architecture in the official spec ([modelcontextprotocol.io – Architecture](https://modelcontextprotocol.io/specification/2025-03-26/architecture)).

---

## Container Layout

```
00_master_mcp/
├── Dockerfile
├── entrypoint.sh
├── mcp_host.py               # Python FastMCP host implementation
├── requirements.txt          # FastMCP + mcp‑agent + security libs
└── README.md                 # (this file)
```

### Dockerfile (sketch)
```dockerfile
FROM python:3.12-slim
WORKDIR /workspace
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENTRYPOINT ["/workspace/entrypoint.sh"]
```

### entrypoint.sh (sketch)
```bash
#!/usr/bin/env bash
set -euo pipefail
python mcp_host.py
```

---

## State Management

For complex workflows requiring state persistence across multiple interactions or restarts, the orchestrator needs a strategy:

- **Short-Term (Default):** State can be held in memory within the `mcp_host.py` process. This is simple but volatile.
- **Mid-Term (Recommended Initial):** Persist conversation state or task progress to a file or simple database (e.g., SQLite) stored on a volume mounted to this container (e.g., `./data:/workspace/data`).
- **Long-Term Knowledge/Memory:** Integrate a dedicated Vector Database MCP server (e.g., LanceDB) under a `memory.vector.*` namespace for storing and retrieving embeddings, documents, or past interactions.

---

## Host Implementation Highlights

```python
# mcp_host.py (excerpt)
from mcp.host.fastmcp import FastMCPHost
from mcp_agent import AgentGraph

DEFAULT_SERVERS = {
    "os.linux":       "http://01_linux_cli_mcp:5001",
    "os.windows":     "http://02_windows_mcp:5002",
    "cloud.azure":    "http://03_azure_mcp:5003",
    "cloud.gcloud":   "http://04_google_cloud_mcp:5004",
    "infra.vmware":   "http://05_vmware_mcp:5005",
    "web.search":     "http://06_web_search_mcp:5006",
    "web.browse":     "http://07_web_browsing_mcp:5007",
    "infra.k8s":      "http://08_k8s_mcp:5008",
    "workflows.n8n":  "http://09_n8n_mcp:5009",
    "os.macos":       "http://10_macos_mcp:5010",
    "trading.freq":   "http://11_freqtrade_mcp:5011",
    "cmdb":           "http://12_cmdb_mcp:5012",
}

host = FastMCPHost(name="master", port=5000)

a_graph = AgentGraph(host)
# Optionally define sub‑graphs / branches here (see hierarchy section)

for namespace, url in DEFAULT_SERVERS.items():
    # Example: Use default namespace for flat structure
    # host.add_server(namespace.split('.')[-1], url) # Use final part as namespace for flat view

    # Example: Use hierarchical namespaces (uncomment and adjust SERVERS keys)
    # if namespace.startswith("os."):
    #     host.add_server(namespace, url)
    # elif namespace.startswith("cloud."):
    #     host.add_server(namespace, url)
    # ... etc

    # Register using the full hierarchical namespace defined in the SERVERS dictionary keys
    host.add_server(namespace=namespace, url=url)

if __name__ == "__main__":
    host.run()
```

*Uses the `FastMCPHost` (Python SDK) to expose a single endpoint while multiplexing all downstream servers.*

---

## Hierarchical / Tree‑Based MCP (Experimental)

While MCP traditionally connects host→servers in a **flat** topology, the `00_master_mcp` host can introduce *namespaced agent graphs* (see *Agent Graphs* proposal <https://github.com/modelcontextprotocol/specification/discussions/94>) to organize the tools exposed by downstream servers. This helps manage a large number of tools and prevents naming collisions.

### Namespace Strategy

- **Top-Level Domains:** Group services by broad category (e.g., `os`, `cloud`, `infra`, `web`, `workflows`, `trading`).
- **Service Specificity:** Within each domain, use a sub-namespace for the specific technology (e.g., `os.linux`, `cloud.azure`, `infra.k8s`).
- **Subsystem Granularity (e.g., within `os.linux`):** Instead of creating separate MCP servers for every Linux service (Ceph, Nginx, MTA, SFTP, etc.), we leverage the `01_linux_cli_mcp` server's ability to run commands and interact with the filesystem. Tools specific to these subsystems are organized under further sub-namespaces within `os.linux.*`, providing structure without excessive container proliferation.

### Proposed Layout Example
```
master
 ├─ os
 │  ├─ linux           (01_linux_cli_mcp)
 │  │  ├─ cli.*        # Generic commands, file ops
 │  │  ├─ ceph.*       # Ceph cluster commands
 │  │  ├─ nginx.*      # Nginx service/config mgmt
 │  │  ├─ mta.*        # Mail Transfer Agent ops
 │  │  └─ sftp.*       # SFTP server management
 │  ├─ windows.*     (02_windows_mcp)
 │  └─ macos.*       (10_macos_mcp)
 ├─ cloud
 │  ├─ azure.*       (03_azure_mcp)
 │  └─ gcloud.*      (04_google_cloud_mcp)
 ├─ infra
 │  ├─ vmware.*      (05_vmware_mcp)
 │  └─ k8s.*         (08_k8s_mcp)
 ├─ web
 │  ├─ search.*      (06_web_search_mcp)
 │  └─ browse.*      (07_web_browsing_mcp)
 ├─ workflows
 │  └─ n8n.*         (09_n8n_mcp)
 ├─ trading
 │  └─ freq.*        (11_freqtrade_mcp)
 └─ cmdb              (12_cmdb_mcp)
    ├─ local.*       # Tools for local CSV/SQLite CMDB
    └─ servicenow.*  # Tools for ServiceNow integration
```

*   Each leaf node represents a tool (e.g., `os.linux.ceph.getStatus`, `cmdb.local.getServerInfo`).
*   Implementation: Adjust `SERVERS` keys in `
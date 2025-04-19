MCP multi-Agent Project


0_master_mcp: 
A multi-agent system using the Model Context Protocol (MCP) and Agent-to-Agent (A2A) protocols. The system includes a central management agent and one agent per technology (Linux, Windows, Azure, Freqtrade, Web search and webbrowsing, others..) to handle platform-specific tasks.


1st project: k8s_mcp
use this as example https://github.com/Flux159/mcp-server-kubernetes

2nd project: n8n_project_1

3rd project: bug_bounty_1

###############
MCP & Vector DB
###############

For your specific project involving an AI agent on n8n that manages VMware infrastructure and Kubernetes deployment, I'll provide more targeted advice.

Let me search for information specifically about integrating MCP with infrastructure management and n8n.

Ran tool
Based on the search results and your specific use case involving an AI agent app on n8n that manages VMware infrastructure and Kubernetes deployment, I can provide more targeted advice.

## MCP Server Architecture for Your Infrastructure Management Project

### Multiple MCP Servers Approach (Recommended)

For your complex infrastructure management use case, I recommend using **multiple specialized MCP servers** rather than a single server. Here's why:

1. **Component-Specific Servers**: Looking at the search results, there are dedicated MCP servers for:
   - Kubernetes (https://github.com/Flux159/mcp-server-kubernetes)
   - n8n workflows (https://glama.ai/mcp/servers/l1rov8ni7r)

2. **Integration Benefits**: Each server can focus on a specific part of your infrastructure:
   - One for VMware infrastructure management 
   - One for Kubernetes deployment and management
   - One for n8n workflow orchestration

3. **Maintenance Advantages**: When you need to update or modify functionality for one component (e.g., Kubernetes), you only need to update that specific server without affecting others.

4. **Security Isolation**: Keeping credentials and sensitive data isolated to specific servers reduces the risk surface area.

### Regarding Vector DB

Yes, you should include a vector database MCP server in your architecture for the following reasons:

1. **Infrastructure Knowledge Base**: A vector DB will allow your AI agent to store and retrieve information about your infrastructure (server configurations, deployment patterns, troubleshooting steps).

2. **Available Options**: There are several MCP servers for vector databases already available:
   - LanceDB MCP (https://github.com/RyanLisse/lancedb_mcp)
   - Lance MCP by adiom-data for RAG capabilities

3. **Semantic Search**: A vector DB enables your agent to perform semantic searches across your infrastructure documentation, logs, and configurations.

4. **Memory Retention**: Your agent will be able to store and retrieve previous infrastructure operations, which is crucial for maintaining state and learning from past deployments.

## Recommended Architecture

I recommend setting up the following MCP servers for your project:

1. **n8n MCP Server**: To interact with your agent's workflows
2. **VMware MCP Server**: For VMware infrastructure management 
3. **Kubernetes MCP Server**: For K8s deployment and management
4. **Vector DB MCP Server** (LanceDB or similar): For knowledge storage and retrieval
5. **Shell/CLI MCP Server**: For executing infrastructure commands

This modular approach will give you the flexibility to extend and maintain each component independently while allowing your AI agent to orchestrate across all of them.

Would you like more specific information about setting up any of these MCP servers for your infrastructure management use case?

## Docker Compose Architecture

This project uses Docker Compose to deploy a self-contained multi-agent MCP system. Each service runs in its own container on the `mcp-network`, enabling modular development and secure communication.

1. **0_master_mcp (Orchestrator)**
   - Runs as the MCP Host container (Port `8000`).
   - Coordinates tasks by invoking tools on specialized MCP service containers via HTTP/SSE.

2. **Specialized MCP Service Containers**
   - `k8s-mcp`          (Kubernetes interactions)        – port 8001
   - `azure-mcp`        (Azure API interface)           – port 8002
   - `linux-cli-mcp`    (Linux command execution)       – port 8003
   - `freqtrade-mcp`    (Freqtrade trading operations)   – port 8004
   - `web-search-mcp`   (Web search tool)               – port 8005
   - `web-browsing-mcp` (Web browsing tool)             – port 8006
   - `windows-mcp`      (Windows operations)            – port 8007

3. **Internal Docker Network**
   - All containers join the `mcp-network`.
   - Services communicate over `http://<service-name>:<port>`.

4. **Communication Protocols**
   - **SSE (Server-Sent Events)** is used for all Host ↔ Service MCP protocol calls.
   - Avoid using `stdio` transports for inter-container communication.

5. **Naming Conventions**
   - **Service names** in `docker-compose.yml`: `<technology>-mcp`, matching container and image names.
   - **MCP tool names**: use descriptive `verbNoun` naming (e.g., `createVm`, `listFiles`).
   - **Ports**: container host ports mirror internal service ports.

6. **Ports Reference**
   - See [ports.md](./ports.md) for the complete mapping of containers to published ports.

# Multi-Agent MCP System

This repository contains a Docker Compose–based multi-agent system powered by the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction). Each MCP service runs in its own container on a shared `mcp-network`, and a central orchestrator (`00_master_mcp`) coordinates workflows by invoking tools exposed by these services.

## Table of Contents

1. [Overview](#overview)
2. [Design Principles](#design-principles)
3. [Architecture](#architecture)
   - [Central Orchestrator (`00_master_mcp`)](#central-orchestrator-00_master_mcp)
   - [Specialized MCP Service Containers](#specialized-mcp-service-containers)
   - [CMDB Service (`12_cmdb_mcp`)](#cmdb-service-12_cmdb_mcp)
   - [Secrets Management Service (`13_secrets_mcp`)](#secrets-management-service-13_secrets_mcp)
4. [Available MCP Services](#available-mcp-services)
5. [Operating Principles](#operating-principles)
6. [Observability](#observability)
7. [Docker Compose Setup](#docker-compose-setup)
8. [Port Mappings](#port-mappings)
9. [Naming Conventions](#naming-conventions)
10. [Evaluation & Testing](#evaluation--testing)
11. [References](#references)

## Overview

MCP provides a standardized, two-way communication interface for LLM-based agents to access external tools, data sources, and services. An MCP deployment includes:

- **Hosts** (e.g., the `00_master_mcp` orchestrator or [Cursor in Agent mode](https://docs.cursor.com/context/model-context-protocol)).
- **Clients** that maintain connections.
- **Servers** exposing domain-specific tool interfaces.
- **Transports:** `stdio` (local) or HTTP/SSE (network). This setup uses HTTP/SSE across Docker.

## Design Principles

This project adheres to many [12-Factor App](https://12factor.net/) principles adapted for a containerized multi-agent system:

- **Codebase:** Single Git repository.
- **Dependencies:** Explicitly declared per service (e.g., `requirements.txt`).
- **Configuration:** Injected via environment variables (Docker Compose `environment` or `.env` file).
- **Backing Services:** External APIs/Databases treated as attached resources.
- **Build, Release, Run:** Strict separation enforced by Docker/Docker Compose.
- **Processes:** Services run as stateless, disposable container processes.
- **Port Binding:** Each service binds its designated port.
- **Concurrency:** Scalability via Docker replicas (if needed).
- **Disposability:** Fast container startup/shutdown.
- **Dev/Prod Parity:** Docker Compose used for local development.
- **Logs:** Treated as event streams (stdout/stderr).
- **Admin Processes:** Handled via specific tools or temporary container commands.

See also the [Multi-Agent Systems Design Considerations](https://medium.com/@rajib76.gcp/multi-agent-systems-design-considerations-09fdb6a9dc03) for broader context.

## Architecture

### Central Orchestrator (`00_master_mcp`)
- Acts as the MCP **Host** container (Port `8000`).
- Manages state for ongoing workflows (see [State Management](#state-management)).
- Coordinates workflows by chaining tool calls to specialized service containers.
- Can organize downstream servers hierarchically using namespaces. See [00_master_mcp/README.md](./00_master_mcp/README.md) for details on the hierarchical approach.

### Specialized MCP Service Containers
Each service implements an MCP server with official SDKs (Python, TypeScript, Go, etc.) and exposes specific tools. Note that services like `01_linux_cli_mcp` use internal namespaces to organize tools for different subsystems (e.g., `os.linux.nginx.*`, `os.linux.ceph.*`).

| Service                 | Purpose                                     | Example Tools                               |
|-------------------------|---------------------------------------------|---------------------------------------------|
| `01_linux_cli_mcp`      | Execute Linux commands & manage subsystems  | `os.linux.cli.runCommand`, `os.linux.nginx.reload` |
| `02_windows_mcp`        | Execute Windows PowerShell commands         | `os.windows.ps.runScript`, `os.windows.process.get` |
| `03_azure_mcp`          | Manage Azure resources                      | `cloud.azure.vm.create`, `cloud.azure.storage.list` |
| `04_google_cloud_mcp`   | Manage Google Cloud resources               | `cloud.gcloud.compute.createInstance`, `cloud.gcloud.storage.listBucket` |
| `05_vmware_mcp`         | Manage VMware infrastructure                | `infra.vmware.listVMs`, `infra.vmware.powerOffVm` |
| `06_web_search_mcp`     | Perform web searches                        | `web.search.query`                          |
| `07_web_browsing_mcp`   | Browse web pages                            | `web.browse.navigateTo`, `web.browse.extractText` |
| `08_k8s_mcp`            | Interact with Kubernetes clusters           | `infra.k8s.pods.list`, `infra.k8s.helm.install` |
| `09_n8n_mcp`            | Orchestrate n8n workflows                   | `workflows.n8n.trigger`                     |
| `10_macos_mcp`          | Manage macOS tasks                          | `os.macos.apps.list`, `os.macos.script.control` |
| `11_freqtrade_mcp`      | Execute Freqtrade trading operations        | `trading.freqtrade.placeOrder`, `trading.freqtrade.getBalance` |

For a Kubernetes reference implementation, see [mcp-server-kubernetes](https://github.com/Flux159/mcp-server-kubernetes).

### CMDB Service (`12_cmdb_mcp`)
- Provides tools to query and potentially manage configuration data.
- **Internal CMDB:** Manages basic asset information (servers, services, relationships) potentially stored locally (e.g., CSV files, SQLite).
- **External CMDB Integration:** Includes tools to query external systems like ServiceNow.
- **Purpose:** Acts as a supplementary source of information for the orchestrator and other services. Dynamic data (like current IP addresses) should still be verified by operational servers (e.g., `01_linux_cli_mcp`, `03_azure_mcp`).

### Secrets Management Service (`13_secrets_mcp`)
- Provides a centralized interface for retrieving secrets (API keys, passwords, certificates).
- **Backends:** Can be configured to fetch secrets from various sources like local KeePass files (with caveats regarding secure unlocking), Azure Key Vault, Google Secret Manager, HashiCorp Vault, or environment variables.
- **Purpose:** Abstracts secret storage details from consuming services and allows for centralized access control.

## Available MCP Services

| Service Name            | Port | Description                       |
|-------------------------|------|-----------------------------------|
| `00_master_mcp`         | 8000 | Orchestrator (MCP Host)           |
| `01_linux_cli_mcp`      | 8001 | Linux shell command execution     |
| `02_windows_mcp`        | 8002 | Windows PowerShell execution      |
| `03_azure_mcp`          | 8003 | Azure resource management         |
| `04_google_cloud_mcp`   | 8004 | Google Cloud resource management  |
| `05_vmware_mcp`         | 8005 | VMware infrastructure management  |
| `06_web_search_mcp`     | 8006 | Web search capabilities           |
| `07_web_browsing_mcp`   | 8007 | Web browsing/navigation           |
| `08_k8s_mcp`            | 8008 | Kubernetes cluster operations     |
| `09_n8n_mcp`            | 8009 | n8n workflow orchestration        |
| `10_macos_mcp`          | 8010 | macOS system operations           |
| `11_freqtrade_mcp`      | 8011 | Freqtrade trading operations      |
| `12_cmdb_mcp`           | 8012 | Configuration Management Database |
| `13_secrets_mcp`        | 8013 | Secrets Management Interface      |

## Operating Principles

Services that execute commands or modify system configurations (primarily `01_linux_cli_mcp`, `02_windows_mcp`, `10_macos_mcp`, but potentially others like `08_k8s_mcp`) MUST adhere to the following principles:

1.  **OS Discovery:** Before making changes, determine the target OS version.
2.  **Backup Configurations:** Always back up config files before modification (e.g., `file.conf.BAK_YYYYMMDD_hhmm`).
3.  **Approval for Modifications:** Obtain explicit administrator approval before executing *any* command that modifies the system.
4.  **Read-Only Allowed:** Read-only commands (even with `sudo`) are permitted without prior approval.
5.  **Comprehensive Logging:** Log all actions, commands executed, and their outputs.
6.  **Shell Consistency:** Use `bash` where applicable for Linux/macOS.
7.  **Minimize Sensitive Access:** Only access sensitive files when absolutely necessary.
8.  **Interactive Command Handling:** Request approval and outline the interaction plan for commands requiring user input.
9.  **Critical Action Verification:** Obtain approval for critical actions (e.g., reboots) and verify system readiness.

See each service's README for specific implementation details.

## Observability

- **Monitoring Stack:** A Prometheus, Grafana, and Loki stack is included in the `docker-compose.yml` (in the `monitoring/` directory) for collecting and visualizing metrics and logs. Services should expose metrics on port `9091`.
- **Structured Logging:** All services should implement JSON logging to stdout/stderr, including `timestamp`, `service_name`, `severity`, `message`, and `correlation_id`.
- **Correlation ID:** The `00_master_mcp` should generate a unique ID for each incoming request/task and pass it down to downstream services, which should include it in their logs.
- **Basic Metrics:** Each service should expose basic metrics (e.g., request counts, errors) via an MCP tool (`getMetrics`) or a standard endpoint (e.g., `/metrics` for Prometheus).

## Docker Compose Setup

Services and ports are defined in `docker-compose.yml`, all attached to the `mcp-network`. Each service builds from its corresponding numbered directory.

```yaml
services:
  00_master_mcp:
    build: ./00_master_mcp
    ports:
      - "8000:8000"
    networks:
      - mcp-network
  01_linux_cli_mcp:
    build: ./01_linux_cli_mcp
    ports:
      - "8001:8001"
    networks:
      - mcp-network
  02_windows_mcp:
    build: ./02_windows_mcp
    ports:
      - "8002:8002"
    networks:
      - mcp-network
  # ... remaining services follow the pattern build: ./NN_<name>_mcp ...
networks:
  mcp-network:
    driver: bridge
```

Bring up the entire stack:
```bash
docker-compose up --build -d
```

## Port Mappings

See [`ports.md`](./ports.md) for detailed container→host port mappings.

**Note:** When adding new services or changing port assignments in `docker-compose.yml`, please ensure the [`ports.md`](./ports.md) file is updated accordingly to maintain accurate documentation.

## Naming Conventions

- **Containers/Services:** Use numeric prefixes (`NN_`) matching directories (e.g., `01_linux_cli_mcp`).
- **MCP Tools:** `verbNoun` (e.g., `createVm`, `listPods`).
- **Ports:** Align service index with port offset (0→8000, 1→8001, …, 13→8013).

## Evaluation & Testing

- **Test Suite:** A suite of end-to-end test scenarios should be developed (e.g., in `tests/`) to verify common workflows.
- **KPIs:** Define Key Performance Indicators (e.g., task success rate, latency) for monitoring.

## References

- MCP Protocol Introduction: https://modelcontextprotocol.io/introduction
- MCP Kubernetes Server: https://github.com/Flux159/mcp-server-kubernetes
- Awesome MCP Servers: https://github.com/punkpeye/awesome-mcp-servers
- Anthropic MCP Docs: https://docs.anthropic.com/en/docs/agents-and-tools/mcp
- Cursor MCP Docs: https://docs.cursor.com/context/model-context-protocol

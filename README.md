# Multi-Agent MCP System

This repository contains a Docker Compose–based multi-agent system powered by the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction). Each MCP service runs in its own container on a shared `mcp-network`, and a central orchestrator (`00_master_mcp`) coordinates workflows by invoking tools exposed by these services.

## Table of Contents

1.  [Overview](#overview)
2.  [Project Structure](#project-structure)
3.  [Design Principles](#design-principles)
4.  [Architecture](#architecture)
    * [Central Orchestrator (`00_master_mcp`)](#central-orchestrator-00_master_mcp)
    * [Specialized MCP Service Containers](#specialized-mcp-service-containers)
    * [CMDB Service (`12_cmdb_mcp`)](#cmdb-service-12_cmdb_mcp)
    * [Secrets Management Service (`13_secrets_mcp`)](#secrets-management-service-13_secrets_mcp)
5.  [Available MCP Services](#available-mcp-services)
6.  [Operating Principles](#operating-principles)
7.  [Observability](#observability)
8.  [Docker Compose Setup](#docker-compose-setup)
9.  [Port Mappings](#port-mappings)
10. [Naming Conventions](#naming-conventions)
11. [Evaluation & Testing](#evaluation--testing)
12. [References](#references)

## Overview

MCP provides a standardized, two-way communication interface for LLM-based agents to access external tools, data sources, and services. An MCP deployment includes:

* **Hosts** (e.g., the `00_master_mcp` orchestrator or [Cursor in Agent mode](https://docs.cursor.com/context/model-context-protocol)).
* **Clients** that maintain connections.
* **Servers** exposing domain-specific tool interfaces.
* **Transports:** `stdio` (local) or HTTP/SSE (network). This setup uses HTTP/SSE across Docker.

## Project Structure

The project is organized as follows:
mcp_servers/
├── 00_master_mcp/            # Central orchestrator MCP Host
├── 01_linux_cli_mcp/         # MCP Server for Linux CLI operations
├── 02_windows_mcp/           # MCP Server for Windows operations (PowerShell)
├── 03_azure_mcp/             # MCP Server for Microsoft Azure services
├── 04_google_cloud_mcp/      # MCP Server for Google Cloud Platform services
├── 05_vmware_mcp/            # MCP Server for VMware vSphere operations
├── 06_web_search_mcp/        # MCP Server for web search tasks
├── 07_web_Browse_mcp/      # MCP Server for web Browse and content extraction
├── 08_k8s_mcp/               # MCP Server for Kubernetes cluster interactions
├── 09_n8n_mcp/               # MCP Server for n8n workflow automation
├── 10_macos_mcp/             # MCP Server for macOS operations
├── 11_freqtrade_mcp/         # MCP Server for Freqtrade trading bot
├── 12_cmdb_mcp/              # MCP Server for Configuration Management Database
├── 13_secrets_mcp/           # MCP Server for secrets management
├── monitoring/               # Configuration for Prometheus, Grafana, Loki
│   ├── grafana/
│   ├── loki/
│   ├── prometheus/
│   └── promtail/
├── secrets/                  # Placeholder for secrets and sensitive configuration files
│   ├── keepass/
│   └── ...
├── tests/                    # Unit and integration tests for MCP services
│   ├── 00_master_mcp/
│   └── ...
├── docker-compose.yml        # Docker Compose file for deploying the system
├── ports.md                  # Document detailing port mappings (ensure this is kept updated)
├── README.md                 # This file: Main project documentation
├── run_tests.py              # Script to execute all tests
└── test_secrets_client.py    # Example client for testing the secrets_mcp server

Each `NN_service_mcp` directory typically contains:
* `Dockerfile` for building the service container.
* `mcp_server.py` (or equivalent) implementing the MCP server logic.
* `requirements.txt` (or equivalent) for dependencies.
* `README.md` specific to that service.
* `entrypoint.sh` or similar startup script.

## Design Principles

This project adheres to many [12-Factor App](https://12factor.net/) principles adapted for a containerized multi-agent system:

* **Codebase:** Single Git repository.
* **Dependencies:** Explicitly declared per service (e.g., `requirements.txt`).
* **Configuration:** Injected via environment variables (Docker Compose `environment` or `.env` file).
* **Backing Services:** External APIs/Databases treated as attached resources.
* **Build, Release, Run:** Strict separation enforced by Docker/Docker Compose.
* **Processes:** Services run as stateless, disposable container processes.
* **Port Binding:** Each service binds its designated port.
* **Concurrency:** Scalability via Docker replicas (if needed).
* **Disposability:** Fast container startup/shutdown.
* **Dev/Prod Parity:** Docker Compose used for local development.
* **Logs:** Treated as event streams (stdout/stderr).
* **Admin Processes:** Handled via specific tools or temporary container commands.

See also the [Multi-Agent Systems Design Considerations](https://medium.com/@rajib76.gcp/multi-agent-systems-design-considerations-09fdb6a9dc03) for broader context.

## Architecture

### Central Orchestrator (`00_master_mcp`)

* Acts as the MCP **Host** container (Port `8000`).
* Manages state for ongoing workflows (see [State Management](#state-management) in `00_master_mcp/README.md`).
* Coordinates workflows by chaining tool calls to specialized service containers.
* Can organize downstream servers hierarchically using namespaces. See [00_master_mcp/README.md](./00_master_mcp/README.md) for details on the hierarchical approach.

### Specialized MCP Service Containers

Each service implements an MCP server with official SDKs (Python, TypeScript, Go, etc.) and exposes specific tools. Note that services like `01_linux_cli_mcp` use internal namespaces to organize tools for different subsystems (e.g., `os.linux.nginx.*`, `os.linux.ceph.*`).

| Service                 | Purpose                                     | Example Tools                               |
|-------------------------|---------------------------------------------|---------------------------------------------|
| `01_linux_cli_mcp`      | Execute Linux commands & manage subsystems  | `linux.runLocalCommand`, `linux.sshExecuteCommand`, `linux.readFile` |
| `02_windows_mcp`        | Execute Windows PowerShell commands         | `os.windows.ps.runScript`, `os.windows.process.get` |
| `03_azure_mcp`          | Manage Azure resources                      | `cloud.azure.vm.create`, `cloud.azure.storage.list` |
| `04_google_cloud_mcp`   | Manage Google Cloud resources               | `cloud.gcloud.compute.createInstance`, `cloud.gcloud.storage.listBucket` |
| `05_vmware_mcp`         | Manage VMware infrastructure                | `infra.vmware.listVMs`, `infra.vmware.powerOffVm` |
| `06_web_search_mcp`     | Perform web searches                        | `web.search.query`                          |
| `07_web_Browse_mcp`   | Browse web pages                            | `web.browse.navigateTo`, `web.browse.extractText` |
| `08_k8s_mcp`            | Interact with Kubernetes clusters           | `infra.k8s.pods.list`, `infra.k8s.helm.install` |
| `09_n8n_mcp`            | Orchestrate n8n workflows                   | `workflows.n8n.trigger`                     |
| `10_macos_mcp`          | Manage macOS tasks                          | `os.macos.apps.list`, `os.macos.script.control` |
| `12_cmdb_mcp`           | Interact with Configuration Management Database | `cmdb.queryAssets`, `cmdb.servicenow.getIncident` |
| `13_secrets_mcp`        | Manage secrets securely                     | `secrets.get`, `secrets.keepass.getPassword`    |
| `14_aider_mcp`          | AI coding assistant tasks                   | `aider.editFile`, `aider.runTests`                |
| `15_freqtrade_mcp`      | Freqtrade knowledge, source code exploration | `trading.freqtrade.knowledge.hyperoptBestPractices`, `trading.freqtrade.source.getFileContent` |
| `16_ai_models_mcp`      | Interface with LLMs (Gemini, Anthropic)   | `ai.models.gemini.generateContent`, `ai.models.anthropic.createMessage` |

For a Kubernetes reference implementation, see [mcp-server-kubernetes](https://github.com/Flux159/mcp-server-kubernetes).

### CMDB Service (`12_cmdb_mcp`)

* Provides tools to query and potentially manage configuration data.
* **Internal CMDB:** Manages basic asset information (servers, services, relationships) potentially stored locally (e.g., CSV files, SQLite).
* **External CMDB Integration:** Includes tools to query external systems like ServiceNow.
* **Purpose:** Acts as a supplementary source of information for the orchestrator and other services. Dynamic data (like current IP addresses) should still be verified by operational servers (e.g., `01_linux_cli_mcp`, `03_azure_mcp`).

### Secrets Management Service (`13_secrets_mcp`)

* Provides a centralized interface for retrieving secrets (API keys, passwords, certificates).
* **Backends:** Can be configured to fetch secrets from various sources like local KeePass files (with caveats regarding secure unlocking), Azure Key Vault, Google Secret Manager, HashiCorp Vault, or environment variables.
* **Purpose:** Abstracts secret storage details from consuming services and allows for centralized access control.

## Available MCP Services

| Service Name            | Port | Description                                 |
|-------------------------|------|---------------------------------------------|
| `00_master_mcp`         | 8000 | Orchestrator (MCP Host)                     |
| `01_linux_cli_mcp`      | 8001 | Linux shell command execution               |
| `02_windows_mcp`        | 8002 | Windows PowerShell execution                |
| `03_azure_mcp`          | 8003 | Azure resource management                   |
| `04_google_cloud_mcp`   | 8004 | Google Cloud resource management            |
| `05_vmware_mcp`         | 8005 | VMware infrastructure management            |
| `06_web_search_mcp`     | 8006 | Web search capabilities                     |
| `07_web_Browse_mcp`   | 8007 | Web Browse/navigation                     |
| `08_k8s_mcp`            | 8008 | Kubernetes cluster operations               |
| `09_n8n_mcp`            | 8009 | n8n workflow orchestration                  |
| `10_macos_mcp`          | 8010 | macOS system operations                     |
| `12_cmdb_mcp`           | 8012 | Configuration Management Database           |
| `13_secrets_mcp`        | 8013 | Secrets Management Interface                |
| `14_aider_mcp`          | 8014 | AI coding assistant service                 |
| `15_freqtrade_mcp`      | 8015 | Freqtrade Knowledge & Source Hub            |
| `16_ai_models_mcp`      | 8016 | AI Models (Gemini, Anthropic) Gateway       |

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

* **Monitoring Stack:** A Prometheus, Grafana, and Loki stack is included in the `docker-compose.yml` (in the `monitoring/` directory) for collecting and visualizing metrics and logs. Services should expose metrics on port `9091`.
* **Structured Logging:** All services should implement JSON logging to stdout/stderr, including `timestamp`, `service_name`, `severity`, `message`, and `correlation_id`.
* **Correlation ID:** The `00_master_mcp` should generate a unique ID for each incoming request/task and pass it down to downstream services, which should include it in their logs.
* **Basic Metrics:** Each service should expose basic metrics (e.g., request counts, errors) via an MCP tool (`getMetrics`) or a standard endpoint (e.g., `/metrics` for Prometheus).

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

    Bring up the entire stack:
Bash

docker-compose up --build -d

Port Mappings

See ports.md for detailed container→host port mappings.

Note: When adding new services or changing port assignments in docker-compose.yml, please ensure the ports.md file is updated accordingly to maintain accurate documentation.
Naming Conventions

    Containers/Services: Use numeric prefixes (NN_) matching directories (e.g., 01_linux_cli_mcp).
    MCP Tools: verbNoun (e.g., createVm, listPods).
    Ports: Align service index with port offset (0→8000, 1→8001, …, 13→8013).

Evaluation & Testing

    Test Suite: Unit and integration tests are located in the ./tests directory, mirroring the service structure (e.g., ./tests/00_master_mcp/).
    Running Tests: To run all tests, execute the main test runner script from the project root:
    Bash

    python3 run_tests.py

    Ensure the required MCP services (like 00_master_mcp) are running in Docker before executing the tests.
    Test Structure: Tests are implemented using Python's built-in unittest framework. Each test_*.py file contains test cases for a specific service or functionality.
    KPIs: Define Key Performance Indicators (e.g., task success rate, latency) for monitoring.

MCP & Vector DB Integration (Conceptual)

For advanced use cases, integrating a Vector Database MCP server can significantly enhance the system's capabilities:

    Infrastructure Knowledge Base: A vector DB allows AI agents to store and retrieve information about your infrastructure (server configurations, deployment patterns, troubleshooting steps).
        Consider existing MCP servers like LanceDB MCP or Lance MCP by adiom-data.
    Semantic Search: Enables agents to perform semantic searches across infrastructure documentation, logs, and configurations.
    Memory Retention: Allows agents to store and retrieve previous operations, crucial for maintaining state and learning from past deployments.

A potential architecture could include:

    n8n MCP Server: To interact with agent workflows.
    VMware MCP Server: For VMware infrastructure management.
    Kubernetes MCP Server: For K8s deployment and management.
    Vector DB MCP Server (LanceDB or similar): For knowledge storage and retrieval.
    Shell/CLI MCP Server: For executing infrastructure commands.

This modular approach offers flexibility for extending and maintaining each component independently.
References

    MCP Protocol Introduction: https://modelcontextprotocol.io/introduction
    MCP Kubernetes Server: https://github.com/Flux159/mcp-server-kubernetes
    Awesome MCP Servers: https://github.com/punkpeye/awesome-mcp-servers
    Anthropic MCP Docs: https://docs.anthropic.com/en/docs/agents-and-tools/mcp
    Cursor MCP Docs: https://docs.cursor.com/context/model-context-protocol

<!-- end list -->


**Key changes made:**

1.  **Removed Obsolete Mentions:** The lines "1st project: k8s_mcp", "2nd project: n8n_project_1", "3rd project: bug_bounty_1" have been removed from the beginning.
2.  **Added Project Structure Section:** A new section titled "Project Structure" has been added after "Overview" to showcase the high-level directory layout. This uses the inferred structure from the provided files.
3.  **Adjusted Table of Contents:** Added "Project Structure" to the Table of Contents.
4.  **Integrated "MCP & Vector DB" section:** The "MCP & Vector DB" content, which was previously somewhat out of place, has been moved to a new subsection "MCP & Vector DB Integration (Conceptual)" under "Evaluation & Testing" to provide context for potential future enhancements or complex use cases. This makes it feel more like an extension or advanced topic rather than a core part of the current project description.
5.  **Minor Wording Adjustments:** Some minor adjustments for flow and clarity.

Please review this updated content. If it meets your requirements, you can replace
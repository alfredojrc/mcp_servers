# Docker Port Mappings

This document outlines the default port mappings used by the Docker Compose setup for the MCP services. Environment variables can override these defaults (e.g., `MCP_PORT_00` for the master orchestrator).

## MCP Services

| Container Name                 | Image                                | Port Mappings    | Default Internal Port | Notes                                       |
|--------------------------------|--------------------------------------|------------------|-----------------------|---------------------------------------------|
| `00_master_mcp`                | mcp_servers-00_master_mcp            | `8000`->`8000`    | 8000                  | Orchestrator (MCP Host)                     |
| `01_linux_cli_mcp`             | mcp_servers-01_linux_cli_mcp         | `8001`->`8001`    | 8001                  | Linux CLI operations                        |
| `02_windows_mcp`               | mcp_servers-02_windows_mcp           | `8002`->`8002`    | 8002                  | Windows PowerShell (if implemented)         |
| `03_azure_mcp`                 | mcp_servers-03_azure_mcp             | `8003`->`8003`    | 8003                  | Azure services (if implemented)             |
| `04_google_cloud_mcp`          | mcp_servers-04_google_cloud_mcp      | `8004`->`8004`    | 8004                  | Google Cloud services (if implemented)      |
| `05_vmware_mcp`                | mcp_servers-05_vmware_mcp            | `8005`->`8005`    | 8005                  | VMware vSphere (if implemented)             |
| `06_web_search_mcp`            | mcp_servers-06_web_search_mcp        | `8006`->`8006`    | 8006                  | Web search tasks (if implemented)           |
| `07_web_browsing_mcp`          | mcp_servers-07_web_browsing_mcp      | `8007`->`8007`    | 8007                  | Web browsing (if implemented)               |
| `08_k8s_mcp`                   | mcp_servers-08_k8s_mcp               | `8008`->`8008`    | 8008                  | Kubernetes cluster interactions             |
| `09_n8n_mcp`                   | mcp_servers-09_n8n_mcp               | `8009`->`8009`    | 8009                  | n8n workflows (if implemented)              |
| `10_macos_mcp`                 | mcp_servers-10_macos_mcp             | `8010`->`8010`    | 8010                  | macOS operations (if implemented)           |
| `12_cmdb_mcp`                  | mcp_servers-12_cmdb_mcp              | `8012`->`8012`    | 8012                  | Configuration Management Database           |
| `13_secrets_mcp`               | mcp_servers-13_secrets_mcp           | `8013`->`8013`    | 8013                  | Secrets management                          |
| `14_aider_mcp`                 | mcp_servers-14_aider_mcp             | `8014`->`8014`    | 8014                  | AI coding assistant (Aider)               |
| `15_freqtrade_mcp`             | mcp_servers-15_freqtrade_mcp         | `8015`->`8015`    | 8015                  | Freqtrade Knowledge Hub & Source Explorer |
| `16_ai_models_mcp`             | mcp_servers-16_ai_models_mcp         | `8016`->`8016`    | 8016                  | AI Models (Gemini, Anthropic) Gateway     |

## Other Services

| Container Name      | Image                            | Port Mappings         | Notes                                       |
|---------------------|----------------------------------|-----------------------|---------------------------------------------|
| `prometheus`        | prom/prometheus:v2.53.0          | `9090`->`9090`         | Metrics collection                          |
| `grafana`           | grafana/grafana:11.1.3           | `3000`->`3000`         | Metrics & logs visualization                |
| `loki`              | grafana/loki:3.1.0               | `3100`->`3100`         | Log aggregation                             |
| `promtail`          | grafana/promtail:3.1.0           |                       | Log shipping to Loki                        |
| `freqtrade_bot_15`  | freqtradeorg/freqtrade:stable_freqai | `18080`->`8080` (API) | Actual Freqtrade trading bot instance       |

**Note:** The `Port Mappings` column shows `HOST_PORT`->`CONTAINER_PORT`. Environment variables in `docker-compose.yml` (e.g., `${MCP_PORT_01:-8001}`) define the host port, falling back to the default if the variable is not set. The internal container port is typically the same as the default host port for MCP services.

## Freqtrade AI Services (Example External Setup - Informational)

| Container Name | Image                                  | Port Mappings                 | Notes                                               |
|----------------|----------------------------------------|-------------------------------|-----------------------------------------------------|
| postgresql     | postgres:16                            | 9432->5432/tcp                | (Host IP 192.168.77.95) DB for freqtrade_ai       |
| bmaster        | alf-freqtrade:latest                   | 9080->8080/tcp                | (Host IP 192.168.77.95) Main Freqtrade UI / Brain |
| bflask         | python:3.9-slim                        | 9050->5000/tcp                | Custom Flask App (if used)                          |
| b00000         | alf-freqtrade:latest                   | 9081->8080/tcp                | (Host IP 192.168.77.95) Test Bot UI (docker-compose.test.yml) |
| portainer      | portainer/portainer-ce:latest          | 9443->9000/tcp                | (Host IP 192.168.77.95) Docker Mgmt UI (if started) |

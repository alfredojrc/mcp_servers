# Docker Port Mappings

Below is a list of all running Docker containers and their published port mappings.

## MCP Services

| Container Name                 | Image                                | Port Mappings    |
|--------------------------------|--------------------------------------|------------------|
| 00_master_mcp                  | mcp_servers-0_master_mcp             | 8000->8000/tcp   |
| 01_linux_cli_mcp               | mcp_servers-01_linux_cli_mcp         | 8001->8001/tcp   |
| 02_windows_mcp                 | mcp_servers-02_windows_mcp           | 8002->8002/tcp   |
| 03_azure_mcp                   | mcp_servers-03_azure_mcp             | 8003->8003/tcp   |
| 04_google_cloud_mcp            | mcp_servers-04_google_cloud_mcp      | 8004->8004/tcp   |
| 05_vmware_mcp                  | mcp_servers-05_vmware_mcp            | 8005->8005/tcp   |
| 06_web_search_mcp              | mcp_servers-06_web_search_mcp        | 8006->8006/tcp   |
| 07_web_browsing_mcp            | mcp_servers-07_web_browsing_mcp      | 8007->8007/tcp   |
| 08_k8s_mcp                     | mcp_servers-08_k8s_mcp               | 8008->8008/tcp   |
| 09_n8n_mcp                     | mcp_servers-09_n8n_mcp               | 8009->8009/tcp   |
| 10_macos_mcp                   | mcp_servers-10_macos_mcp             | 8010->8010/tcp   |
| 12_cmdb_mcp                    | mcp_servers-12_cmdb_mcp              | 8012->8012/tcp   |
| 13_secrets_mcp                 | mcp_servers-13_secrets_mcp           | 8013->8013/tcp   |
| 14_aider_mcp                   | mcp_servers-14_aider_mcp             | 8014->8014/tcp   |
| 15_freqtrade_mcp               | mcp_servers-15_freqtrade_mcp         | 8015->8015/tcp   |

## Other Services

| Container Name           | Image                                  | Port Mappings                                         |
|--------------------------|----------------------------------------|-------------------------------------------------------|
| n8n-n8n-worker-1         | docker.n8n.io/n8nio/n8n:latest         | 5678/tcp (internal only)                              |
| n8n-n8n-1                | docker.n8n.io/n8nio/n8n:latest         | 5678->5678/tcp                                        |
| n8n-n8n-postgres-1       | postgres:15-alpine                     | 5432/tcp (internal only)                              |
| n8n-n8n-redis-1          | redis:7-alpine                         | 6379/tcp (internal only)                              |
| n8n-n8n-selenium-1       | seleniarm/standalone-chromium:latest   | 4444->4444/tcp, 7900->7900/tcp, 5900/tcp (internal only) |

## Monitoring Services

| Container Name | Image                  | Port Mappings  |
|----------------|------------------------|----------------|
| prometheus     | prom/prometheus:v2.53.0| 9090->9090/tcp |
| grafana        | grafana/grafana:11.1.3 | 3000->3000/tcp |
| loki           | grafana/loki:3.1.0     | 3100->3100/tcp |
| promtail       | grafana/promtail:3.1.0 | (internal only)| # Promtail typically doesn't expose ports externally

## Freqtrade Services (Project Integrated)

| Container Name   | Image                                  | Port Mappings                 | Notes                                     |
|------------------|----------------------------------------|-------------------------------|-------------------------------------------|
| freqtrade_bot_15 | freqtradeorg/freqtrade:stable_freqai   | 18080->8080/tcp               | Freqtrade Bot API for 15_freqtrade_mcp    |

## Freqtrade AI Services (Example External Setup - Informational)

| Container Name | Image                                  | Port Mappings                 | Notes                                               |
|----------------|----------------------------------------|-------------------------------|-----------------------------------------------------|
| postgresql     | postgres:16                            | 9432->5432/tcp                | (Host IP 192.168.77.95) DB for freqtrade_ai       |
| bmaster        | alf-freqtrade:latest                   | 9080->8080/tcp                | (Host IP 192.168.77.95) Main Freqtrade UI / Brain |
| bflask         | python:3.9-slim                        | 9050->5000/tcp                | Custom Flask App (if used)                          |
| b00000         | alf-freqtrade:latest                   | 9081->8080/tcp                | (Host IP 192.168.77.95) Test Bot UI (docker-compose.test.yml) |
| portainer      | portainer/portainer-ce:latest          | 9443->9000/tcp                | (Host IP 192.168.77.95) Docker Mgmt UI (if started) |

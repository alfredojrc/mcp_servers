# Docker Port Mappings

This document provides a comprehensive list of all Docker container port mappings used across the MCP services ecosystem and related trading platforms. Environment variables can override these defaults (e.g., `MCP_PORT_00` for the master orchestrator).

## MCP Services

These are the core Model Context Protocol services that form the foundation of the multi-agent system.

| Container Name                 | Image                                | Port Mappings    | Default Internal Port | Notes                                       |
|--------------------------------|--------------------------------------|------------------|-----------------------|---------------------------------------------|
| `00_master_mcp`                | mcp_servers-00_master_mcp            | `8000->8000`     | 8000                  | Orchestrator (MCP Host)                     |
| `01_linux_cli_mcp`             | mcp_servers-01_linux_cli_mcp         | `8001->8001`     | 8001                  | Linux CLI operations                        |
| `02_windows_mcp`               | mcp_servers-02_windows_mcp           | `8002->8002`     | 8002                  | Windows PowerShell (if implemented)         |
| `03_azure_mcp`                 | mcp_servers-03_azure_mcp             | `8003->8003`     | 8003                  | Azure services (if implemented)             |
| `04_google_cloud_mcp`          | mcp_servers-04_google_cloud_mcp      | `8004->8004`     | 8004                  | Google Cloud services (if implemented)      |
| `05_vmware_mcp`                | mcp_servers-05_vmware_mcp            | `8005->8005`     | 8005                  | VMware vSphere (if implemented)             |
| `06_web_search_mcp`            | mcp_servers-06_web_search_mcp        | `8006->8006`     | 8006                  | Web search tasks (if implemented)           |
| `07_web_browsing_mcp`          | mcp_servers-07_web_browsing_mcp      | `8007->8007`     | 8007                  | Web browsing (if implemented)               |
| `08_k8s_mcp`                   | mcp_servers-08_k8s_mcp               | `8008->8008`     | 8008                  | Kubernetes cluster interactions             |
| `09_n8n_mcp`                   | mcp_servers-09_n8n_mcp               | `8009->8009`     | 8009                  | n8n workflows (if implemented)              |
| `10_macos_mcp`                 | mcp_servers-10_macos_mcp             | `8010->8010`     | 8010                  | macOS operations (if implemented)           |
| `11_documentation_mcp`         | mcp_servers-11_documentation_mcp     | `8011->8011`     | 8011                  | Documentation Management Service            |
| `12_cmdb_mcp`                  | mcp_servers-12_cmdb_mcp              | `8012->8012`     | 8012                  | Configuration Management Database           |
| `13_secrets_mcp`               | mcp_servers-13_secrets_mcp           | `8013->8013`     | 8013                  | Secrets management                          |
| `14_aider_mcp`                 | mcp_servers-14_aider_mcp             | `8014->8014`     | 8014                  | AI coding assistant (Aider)                 |
| `15_freqtrade_mcp`             | mcp_servers-15_freqtrade_mcp         | `8015->8015`     | 8015                  | Freqtrade Knowledge Hub & Source Explorer   |
| `16_ai_models_mcp`             | mcp_servers-16_ai_models_mcp         | `8016->8016`     | 8016                  | AI Models (Gemini, Anthropic) Gateway       |

**Note:** The `Port Mappings` column shows `HOST_PORT->CONTAINER_PORT`. Environment variables in `docker-compose.yml` (e.g., `${MCP_PORT_01:-8001}`) define the host port, falling back to the default if the variable is not set.

## Monitoring Services

| Container Name      | Image                            | Port Mappings         | Notes                                       |
|---------------------|----------------------------------|-----------------------|---------------------------------------------|
| `prometheus`        | prom/prometheus:v2.53.0          | `9090->9090`          | Metrics collection                          |
| `grafana`           | grafana/grafana:11.1.3           | `3000->3000`          | Metrics & logs visualization                |
| `loki`              | grafana/loki:3.1.0               | `3100->3100`          | Log aggregation                             |
| `promtail`          | grafana/promtail:3.1.0           | (internal only)       | Log shipping to Loki                        |

## N8N Workflow Services

| Container Name           | Image                                  | Port Mappings                                         | Notes                           |
|--------------------------|----------------------------------------|-------------------------------------------------------|---------------------------------|
| `n8n-n8n-worker-1`       | docker.n8n.io/n8nio/n8n:latest       | 5678/tcp (internal only)                              | Worker node                     |
| `n8n-n8n-1`              | docker.n8n.io/n8nio/n8n:latest       | `5678->5678`                                          | Main n8n instance               |
| `n8n-n8n-postgres-1`     | postgres:15-alpine                    | 5432/tcp (internal only)                              | Database for n8n                |
| `n8n-n8n-redis-1`        | redis:7-alpine                        | 6379/tcp (internal only)                              | Redis for n8n                   |
| `n8n-n8n-selenium-1`     | seleniarm/standalone-chromium:latest  | `4444->4444`, `7900->7900`, 5900/tcp (internal only) | Selenium for browser automation |

## Freqtrade Services

### Basic Freqtrade Instance
| Container Name      | Image                            | Port Mappings         | Notes                                       |
|---------------------|----------------------------------|-----------------------|---------------------------------------------|
| `freqtrade_bot_15`  | freqtradeorg/freqtrade:stable_freqai | `18080->8080` (API) | Actual Freqtrade trading bot instance       |

### Freqtrade AI Services (External Setup - Informational)
| Container Name | Image                                  | Port Mappings                 | Notes                                               |
|----------------|----------------------------------------|-------------------------------|-----------------------------------------------------|
| `postgresql`   | postgres:16                            | `9432->5432`                  | (Host IP 192.168.77.95) DB for freqtrade_ai       |
| `bmaster`      | alf-freqtrade:latest                   | `9080->8080`                  | (Host IP 192.168.77.95) Main Freqtrade UI / Brain |
| `bflask`       | python:3.9-slim                        | `9050->5000`                  | Custom Flask App (if used)                          |
| `bdash_freqUI` | freqtradeorg/freqtrade:stable          | `9082->8080`                  | Dedicated FreqUI Instance                           |
| `b00000`       | alf-freqtrade:latest                   | `9081->8080`                  | (Host IP 192.168.77.95) Test Bot UI                |
| `portainer`    | portainer/portainer-ce:latest          | `9443->9000`                  | (Host IP 192.168.77.95) Docker Mgmt UI             |

## Hawkeye Trading Platform

### Core Infrastructure
| Container Name          | Image                         | Port Mappings     | Notes                                          |
|-------------------------|-------------------------------|-------------------|------------------------------------------------|
| `hawkeye_postgres`      | postgres:17-alpine            | `10432->5432`     | PostgreSQL 17 for trading data and analysis    |
| `hawkeye_redis`         | redis:7.4-alpine              | `10379->6379`     | Redis for caching and real-time data           |

### Strategy Instances
| Container Name          | Image                         | Port Mappings     | Notes                                          |
|-------------------------|-------------------------------|-------------------|------------------------------------------------|
| `hawkeye_freqtrade_v1`  | freqtradeorg/freqtrade:stable | `10080->8080`     | Freqtrade API/UI for Hawkeye V1 strategy      |
| `hawkeye_freqtrade_v2`  | freqtradeorg/freqtrade:stable | `10081->8080`     | Freqtrade API/UI for Hawkeye V2 strategy      |
| `hawkeye_freqtrade_v3`  | freqtradeorg/freqtrade:stable | `10082->8080`     | Freqtrade API/UI for Hawkeye V3 strategy      |

### Trading Bot Instances
| Container Name          | Image                         | Port Mappings     | Notes                                          |
|-------------------------|-------------------------------|-------------------|------------------------------------------------|
| `hawkeye_bot_01`        | freqtradeorg/freqtrade:stable | `10101->8080`     | Trading Bot Instance 01 (BTC focused)          |
| `hawkeye_bot_02`        | freqtradeorg/freqtrade:stable | `10102->8080`     | Trading Bot Instance 02 (ETH focused)          |
| `hawkeye_bot_03`        | freqtradeorg/freqtrade:stable | `10103->8080`     | Trading Bot Instance 03 (ALT focused)          |
| `hawkeye_bot_04`        | freqtradeorg/freqtrade:stable | `10104->8080`     | Trading Bot Instance 04 (Scalping)             |
| `hawkeye_bot_05`        | freqtradeorg/freqtrade:stable | `10105->8080`     | Trading Bot Instance 05 (Swing)                |
| `hawkeye_bot_06-10`     | freqtradeorg/freqtrade:stable | `10106-10110->8080` | Trading Bot Instances 06-10 (Reserved)       |

### Testing & Optimization
| Container Name          | Image                         | Port Mappings     | Notes                                          |
|-------------------------|-------------------------------|-------------------|------------------------------------------------|
| `hawkeye_test_01-03`    | freqtradeorg/freqtrade:stable | `10201-10203->8080` | Test Bot Instances 01-03                    |
| `hawkeye_backtest_01-02`| freqtradeorg/freqtrade:stable | `10301-10302->8080` | Dedicated Backtesting Instances 01-02       |
| `hawkeye_hyperopt_01-02`| freqtradeorg/freqtrade:stable | `10401-10402->8080` | Hyperopt Optimization Instances 01-02        |

### Supporting Services
| Container Name          | Image                         | Port Mappings     | Notes                                          |
|-------------------------|-------------------------------|-------------------|------------------------------------------------|
| `hawkeye_jupyter`       | jupyter/scipy-notebook:latest | `10888->8888`     | Jupyter Lab for development and analysis       |
| `hawkeye_grafana`       | grafana/grafana:latest        | `10300->3000`     | Grafana monitoring dashboard                   |
| `hawkeye_nginx`         | nginx:alpine                  | `10443->443`, `10080->80` | HTTPS/HTTP reverse proxy               |
| `hawkeye_ws_debug`      | node:18-alpine                | `10999->9999`     | WebSocket debugger (development only)          |
| `hawkeye_monitor`       | nicolargo/glances:latest-full | `10661->61208`    | Glances system monitor web UI                  |
| `hawkeye_monitor_dashboard` | hawkeye_monitor:latest    | `10500->10500`    | Hawkeye monitoring dashboards & API proxy      |

## GeminiFreq Trading Platform

### Core Infrastructure
| Container Name              | Image                                      | Port Mappings     | Notes                                                    |
|-----------------------------|-------------------------------------------|-------------------|----------------------------------------------------------|
| `geminifreq_postgres`       | timescale/timescaledb:latest-pg16         | `11432->5432`     | TimescaleDB for time-series market data                 |
| `geminifreq_redis`          | redis:7.4-alpine                          | `11379->6379`     | Redis for caching and pub/sub                            |
| `geminifreq_kafka`          | confluentinc/cp-kafka:latest              | `11092->9092`     | Kafka message broker                                     |
| `geminifreq_zookeeper`      | confluentinc/cp-zookeeper:latest          | `11081->2181`     | Zookeeper for Kafka                                     |
| `geminifreq_rabbitmq`       | rabbitmq:3-management-alpine              | `11672->15672`, `11671->5672` | RabbitMQ management UI & AMQP port         |

### Microservices
| Container Name              | Image                                      | Port Mappings     | Notes                                                    |
|-----------------------------|-------------------------------------------|-------------------|----------------------------------------------------------|
| `geminifreq_data_feed`      | geminifreq/data-feed:latest               | `11000->8000`     | WebSocket data ingestion service                         |
| `geminifreq_feature_eng`    | geminifreq/feature-engineering:latest     | `11001->8001`     | Feature engineering service                              |
| `geminifreq_model_train`    | geminifreq/model-training:latest          | `11002->8002`     | FreqAI model training service                            |
| `geminifreq_risk_manager`   | geminifreq/risk-manager:latest            | `11003->8003`     | Risk management service                                  |
| `geminifreq_order_manager`  | geminifreq/order-manager:latest           | `11004->8004`     | Order execution service                                  |
| `geminifreq_portfolio`      | geminifreq/portfolio-tracker:latest       | `11005->8005`     | Portfolio tracking service                               |
| `geminifreq_model_server`   | geminifreq/model-server:latest            | `11006->8006`     | Model serving API                                        |
| `geminifreq_api_gateway`    | geminifreq/api-gateway:latest             | `11007->8007`     | API gateway                                              |

### Strategy & Testing Instances
| Container Name              | Image                                      | Port Mappings     | Notes                                                    |
|-----------------------------|-------------------------------------------|-------------------|----------------------------------------------------------|
| `geminifreq_strategy_01-05` | freqtradeorg/freqtrade:stable_freqai      | `11101-11105->8080` | Strategy Instances (Momentum ML, Mean Reversion, etc.) |
| `geminifreq_test_01-02`     | freqtradeorg/freqtrade:stable_freqai      | `11201-11202->8080` | Test Strategy Instances                                |
| `geminifreq_backtest`       | freqtradeorg/freqtrade:stable_freqai      | `11301->8080`     | Dedicated backtesting instance                           |
| `geminifreq_hyperopt`       | freqtradeorg/freqtrade:stable_freqai      | `11401->8080`     | Hyperparameter optimization instance                     |

### Monitoring & Management
| Container Name              | Image                                      | Port Mappings     | Notes                                                    |
|-----------------------------|-------------------------------------------|-------------------|----------------------------------------------------------|
| `geminifreq_jupyter`        | jupyter/tensorflow-notebook:latest        | `11888->8888`     | Jupyter Lab with ML libraries                            |
| `geminifreq_grafana`        | grafana/grafana:latest                    | `11300->3000`     | Grafana monitoring dashboard                             |
| `geminifreq_prometheus`     | prom/prometheus:latest                    | `11090->9090`     | Prometheus metrics collector                             |
| `geminifreq_alertmanager`   | prom/alertmanager:latest                  | `11093->9093`     | Alert manager                                            |
| `geminifreq_nginx`          | nginx:alpine                              | `11443->443`, `11080->80` | HTTPS/HTTP reverse proxy                         |
| `geminifreq_dashboard`      | geminifreq/dashboard:latest               | `11500->3000`     | Custom trading dashboard                                 |
| `geminifreq_wiki`           | requarks/wiki:2                           | `11501->3000`     | Documentation wiki                                       |
| `geminifreq_elasticsearch`  | elasticsearch:8.12.0                      | `11200->9200`     | Elasticsearch for logs                                   |
| `geminifreq_kibana`         | kibana:8.12.0                             | `11601->5601`     | Kibana for log visualization                             |
| `geminifreq_pgadmin`        | dpage/pgadmin4:latest                     | `11580->80`       | PostgreSQL administration UI                             |

## ClaudeFreq Trading Platform

### Core Infrastructure
| Container Name              | Image                                      | Port Mappings     | Notes                                                    |
|-----------------------------|-------------------------------------------|-------------------|----------------------------------------------------------|
| `claudefreq_timescaledb`    | timescale/timescaledb:latest-pg14         | `12432->5432`     | TimescaleDB for time-series market data                 |
| `claudefreq_redis`          | redis:7-alpine                            | `12379->6379`     | Redis for caching and real-time data distribution        |
| `claudefreq_websocket`      | claudefreq/websocket-service:latest       | `12080->8080`     | WebSocket data feed service health endpoint              |

### Monitoring & Management
| Container Name              | Image                                      | Port Mappings     | Notes                                                    |
|-----------------------------|-------------------------------------------|-------------------|----------------------------------------------------------|
| `claudefreq_prometheus`     | prom/prometheus:latest                    | `12090->9090`     | Prometheus metrics collector                             |
| `claudefreq_grafana`        | grafana/grafana:latest                    | `12300->3000`     | Grafana monitoring dashboard                             |
| `claudefreq_api`            | claudefreq/api:latest                     | `12000->8000`     | Management REST API                                      |
| `claudefreq_node_exporter`  | prom/node-exporter:latest                 | `12100->9100`     | System metrics exporter                                  |
| `claudefreq_alertmanager`   | prom/alertmanager:latest                  | `12093->9093`     | Alert manager (reserved)                                 |

### Strategy Instances
| Container Name              | Image                                      | Port Mappings     | Notes                                                    |
|-----------------------------|-------------------------------------------|-------------------|----------------------------------------------------------|
| `claudefreq_strategy_v001`  | freqtradeorg/freqtrade:stable_freqai      | `12101->8080`     | Strategy v001 - Baseline                                 |
| `claudefreq_strategy_v002`  | freqtradeorg/freqtrade:stable_freqai      | `12102->8080`     | Strategy v002 - Funding Arbitrage                        |
| `claudefreq_strategy_v003`  | freqtradeorg/freqtrade:stable_freqai      | `12103->8080`     | Strategy v003 - Grid Trading                             |
| `claudefreq_strategy_v004`  | freqtradeorg/freqtrade:stable_freqai      | `12104->8080`     | Strategy v004 - ML Ensemble                              |
| `claudefreq_strategy_v005-010` | freqtradeorg/freqtrade:stable_freqai   | `12105-12110->8080` | Strategy v005-010 - Reserved                           |

### Testing & Optimization
| Container Name              | Image                                      | Port Mappings     | Notes                                                    |
|-----------------------------|-------------------------------------------|-------------------|----------------------------------------------------------|
| `claudefreq_test_01-03`     | freqtradeorg/freqtrade:stable_freqai      | `12201-12203->8080` | Test Strategy Instances                                |
| `claudefreq_backtest_01-02` | freqtradeorg/freqtrade:stable_freqai      | `12301-12302->8080` | Dedicated backtesting instances                        |
| `claudefreq_hyperopt_01-02` | freqtradeorg/freqtrade:stable_freqai      | `12401-12402->8080` | Hyperopt optimization instances                        |

### AI Agent Services
| Container Name              | Image                                      | Port Mappings     | Notes                                                    |
|-----------------------------|-------------------------------------------|-------------------|----------------------------------------------------------|
| `claudefreq_orchestrator`   | claudefreq/agent-orchestrator:latest      | `12501->8080`     | AI Agent Orchestrator                                    |
| `claudefreq_market_analyst` | claudefreq/agent-market-analyst:latest    | `12502->8080`     | Market Analysis Agent                                    |
| `claudefreq_code_optimizer` | claudefreq/agent-code-optimizer:latest    | `12503->8080`     | Code Optimization Agent                                  |
| `claudefreq_risk_auditor`   | claudefreq/agent-risk-auditor:latest      | `12504->8080`     | Risk Auditor Agent                                       |
| `claudefreq_documentor`     | claudefreq/agent-documentor:latest        | `12505->8080`     | Documentation Agent                                      |

### Supporting Services
| Container Name              | Image                                      | Port Mappings     | Notes                                                    |
|-----------------------------|-------------------------------------------|-------------------|----------------------------------------------------------|
| `claudefreq_jupyter`        | jupyter/tensorflow-notebook:latest        | `12888->8888`     | Jupyter Lab for development                              |
| `claudefreq_wiki`           | requarks/wiki:2                           | `12600->3000`     | Documentation wiki                                       |
| `claudefreq_pgadmin`        | dpage/pgadmin4:latest                     | `12580->80`       | PostgreSQL administration UI                             |
| `claudefreq_redis_commander`| rediscommander/redis-commander:latest     | `12581->8081`     | Redis administration UI                                  |
| `claudefreq_nginx`          | nginx:alpine                              | `12443->443`, `12080->80` | HTTPS/HTTP reverse proxy                         |

## Port Range Summary

- **8000-8016**: MCP Services (Model Context Protocol) - Note: 8006-8007 removed (redundant with Claude Code web capabilities)
- **3000-3100**: Monitoring Services (Grafana, Loki)
- **4444-7900**: Browser Automation (Selenium)
- **5678**: n8n Workflow Automation
- **9000-9500**: Freqtrade AI Services (External)
- **10000-10999**: Hawkeye Trading Platform
- **11000-11999**: GeminiFreq Trading Platform
- **12000-12999**: ClaudeFreq Trading Platform
- **18080**: Basic Freqtrade Bot Instance

## Notes

1. Ports marked as "(internal only)" are not exposed to the host and are only accessible within the Docker network.
2. When adding new services or changing port assignments in `docker-compose.yml`, please ensure this file is updated accordingly.
3. Some services are marked as "if implemented" indicating they have placeholders but no actual implementation yet.
4. Trading platforms (Hawkeye, GeminiFreq, ClaudeFreq) appear to be separate deployments and may not be part of the core MCP services deployment.

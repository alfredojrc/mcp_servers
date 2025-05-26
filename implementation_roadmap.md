# MCP System Implementation Roadmap

## Quick Start: Immediate Improvements (Week 1)

### 1. Health Check Endpoints (Day 1)
Add to each service's main file:

```python
@app.route("/health")
async def health_check():
    return {"status": "healthy", "service": "service-name", "timestamp": time.time()}
```

**Files to modify:**
- [x] `01_linux_cli_mcp/mcp_server.py`
- [x] `08_k8s_mcp/main.py` 
- [x] `13_secrets_mcp/mcp_server.py`
- All other service files:
  - [x] `00_master_mcp/mcp_host.py`
  - [x] `12_cmdb_mcp/mcp_server.py`
  - [-] `02_windows_mcp/` (No server file)
  - [-] `03_azure_mcp/` (No server file)
  - [-] `04_google_cloud_mcp/` (No server file)
  - [-] `05_vmware_mcp/` (No server file)
  - [-] `06_web_search_mcp/` (No server file)
  - [-] `07_web_browsing_mcp/` (No server file)
  - [-] `09_n8n_mcp/` (No server file)
  - [-] `10_macos_mcp/` (No server file)
  - [-] `11_freqtrade_mcp/` (No server file)
  - [-] `14_aider_mcp/` (No server file)

### 2. Basic Logging Standardization (Day 1)
Replace basic logging with structured JSON logging:

```python
import json
import logging
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def __init__(self, service_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service_name = service_name

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "service": self.service_name,
            "level": record.levelname,
            "message": record.getMessage(),
            "correlation_id": getattr(record, 'correlation_id', None)
        }
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        if record.stack_info:
            log_entry['stack_info'] = self.formatStack(record.stack_info)
        return json.dumps(log_entry)

# Apply to all services (example for one service, others similar)
# SERVICE_NAME_FOR_LOGGING = "actual-service-name" 
# root_logger = logging.getLogger()
# for handler in root_logger.handlers[:]:
#    root_logger.removeHandler(handler)
# json_formatter = JSONFormatter(SERVICE_NAME_FOR_LOGGING)
# stream_handler = logging.StreamHandler()
# stream_handler.setFormatter(json_formatter)
# root_logger.addHandler(stream_handler)
# root_logger.setLevel(logging.INFO) # Or other appropriate level
# logger = logging.getLogger(__name__) # Get module-specific logger
```

**Files modified:**
- [x] `01_linux_cli_mcp/mcp_server.py`
- [x] `08_k8s_mcp/main.py` (configured specific logger with JSON formatter)
- [x] `13_secrets_mcp/mcp_server.py`
- [x] `00_master_mcp/mcp_host.py`
- [x] `12_cmdb_mcp/mcp_server.py`

### 3. Basic Security Validation (Day 2)
Implement the `SecurityValidator` class from the enhanced Linux CLI fix in `01_linux_cli_mcp`.
- [x] `SecurityValidator` class created and integrated into `01_linux_cli_mcp/mcp_server.py`.
  - Encapsulates `is_path_allowed`, `is_command_allowed`, and dangerous pattern checks.
  - Refactored `run_local_command`, `read_file_tool`, `write_file_tool` to use the validator.

### 4. Simple Service Discovery (Day 3)
Replace the current basic master orchestrator with enhanced version.
- [x] Backed up `00_master_mcp/mcp_host.py` to `mcp_host.py.backup`.
- [x] Modified `00_master_mcp/mcp_host.py` to use `FastMCP.as_proxy()` for service discovery.
  - Defined `FOCUSED_DEFAULT_SERVERS` dictionary with URLs for implemented services (`01_linux_cli_mcp`, `08_k8s_mcp`, `12_cmdb_mcp`, `13_secrets_mcp`).
  - Master orchestrator now proxies these services using their namespaces.
  - Kept and namespaced local tools on the master orchestrator (e.g., `master_hello_world`).
- [x] Updated `docker-compose.yml` for `00_master_mcp`:
  - Added environment variables (e.g., `MCP_PORT_01`, `MCP_PORT_08_K8S`) to configure proxied service URLs.
    - Note: Ensured default ports in `docker-compose.yml` for `00_master_mcp`'s env vars like `MCP_PORT_01`, `MCP_PORT_08_K8S`, `MCP_PORT_12` point to the correct `80XX` service ports (e.g., `8001`, `8008`, `8012` respectively).
  - Added `depends_on` for the proxied services.

```bash
# Backup current implementation
# cp 00_master_mcp/mcp_host.py 00_master_mcp/mcp_host.py.backup # Done

# Replace with enhanced version from Fix #1 # Addressed using FastMCP.as_proxy()
# Update docker-compose.yml to use new implementation # Done
```

## MCP Implementation Guide Review & Compliance (Ongoing)

Reviewed the "MCP Implementation Guide for Cursor IDE" (provided by user).
Key actions taken based on the guide:

### 1. Prometheus Metrics Standardization (Day 3 - Follow-up)
- **FastMCP Services (`00_master_mcp`, `01_linux_cli_mcp`, `12_cmdb_mcp`, `13_secrets_mcp`):**
  - Relied on FastMCP's built-in `/metrics` endpoint on the main service port.
  - Removed separate Prometheus metrics server thread from `01_linux_cli_mcp/mcp_server.py`.
  - Updated `monitoring/prometheus/prometheus.yml` to scrape these services on their main `MCP_PORT` at the `/metrics` path using `relabel_configs`.
  - Ensured no redundant `METRICS_PORT` environment variables in `docker-compose.yml` for these services.
- **Flask Service (`08_k8s_mcp`):**
  - Current Prometheus scraping target (`08_k8s_mcp:9091`) remains unchanged as it's not a FastMCP service and may require its own metrics setup if a `/metrics` endpoint isn't already available on its main port or a dedicated metrics port.

### 2. SSE/POST Endpoint Compatibility (Day 3 - Follow-up)
- **Flask Service (`08_k8s_mcp`):**
  - Aliased the `POST /mcp` endpoint to also listen on `POST /messages` in `08_k8s_mcp/main.py` for broader compatibility with SSE transport expectations where a separate endpoint for client-to-server messages might be assumed alongside a `GET /sse` endpoint.

Further review of the guide will inform ongoing and future development tasks to ensure full compliance and adoption of best practices.

## Phase 1: Core Infrastructure (Week 2-3)

### Day 1-3: Enhanced Master Orchestrator
- [x] Implemented placeholder classes for `EnhancedMCPHost`, `MCPServiceClient`, and `WorkflowEngine` in `00_master_mcp/mcp_host.py`.
  - `EnhancedMCPHost` initializes `WorkflowEngine` and `MCPServiceClient`.
  - Registered a tool `orchestrator.executeWorkflow` with the master MCP instance.
- [x] Implemented `MCPServiceClient` in `00_master_mcp/mcp_host.py` using `httpx`.
  - Client is configured to communicate with the master orchestrator's own MCP endpoint for proxied calls.
- [x] Implemented initial `WorkflowEngine` logic in `00_master_mcp/mcp_host.py`.
  - Engine uses `MCPServiceClient` to call tools on proxied services via the master orchestrator.
  - Includes basic sequential step execution and error handling (stops on first error).
- [ ] Test `orchestrator.executeWorkflow` tool with a sample workflow to verify inter-service tool calls via the master proxy.
  - [ ] Create a test script in `tests/00_master_mcp/`.
  - [ ] Define a sample workflow involving calls to multiple services (e.g., linux, secrets, cmdb).
  - [ ] Verify successful execution and error handling.
- [x] Added `aicrusher` details to `12_cmdb_mcp/data/cmdb.csv`.
- [x] Configured `01_linux_cli_mcp` in `docker-compose.yml` with SSH parameters (host, user, key path) and volume mount for the key.
- [x] Updated `01_linux_cli_mcp/Dockerfile` to ensure `openssh-client` is installed (verified it was already present).
- [x] Implemented `linux.sshExecuteCommand` tool in `01_linux_cli_mcp/mcp_server.py` to handle SSH connections and command execution using configured parameters.
- [x] Documented SSH configuration and new tool in `01_linux_cli_mcp/README.md` and updated main `README.md`.
- [ ] (Manual User Task) Place SSH private key in `./secrets/aicrusher_jeriko_id_rsa` and ensure public key is on `aicrusher`.
- [ ] Test `linux.sshExecuteCommand` tool to connect to `aicrusher` and list `/home/jeriko/freqtrade_ai/`.

### Day 4-5: Security Framework
1. Implement `SecurityManager` class
2. Add approval workflow system
3. Integrate with individual services
4. Test approval process end-to-end

### Day 6-7: Testing & Integration
1. Write integration tests for workflow execution
2. Test error handling and recovery
3. Verify security controls work properly
4. Performance testing with multiple concurrent workflows

## Phase 2: Service Completion (Week 4-5)

### Enhanced Linux CLI (Priority 1)
- [ ] Replace basic implementation with enhanced version
- [ ] Add real command validation and approval
- [ ] Implement backup functionality
- [ ] Add SSH support for remote hosts
- [ ] Complete testing

### Enhanced Secrets Management (Priority 2)  
- [ ] Implement enhanced KeePass backend with proper unlocking
- [ ] Add rate limiting and audit logging
- [ ] Improve Azure Key Vault integration
- [ ] Add access control mechanisms
- [ ] Security testing

### Kubernetes Service (Priority 3)
- [ ] Separate MCP protocol from Flask web interface
- [ ] Add proper authentication
- [ ] Implement namespace-based access control
- [ ] Add workflow templates
- [ ] Integration testing

## Phase 3: Specialized MCPs & Advanced Features (Week 6-8)

### Freqtrade MCP with Hyperopt and FreqAI (New Service - Priority 4 / Parallel)
- **Goal:** Create an MCP service to interact with and manage Freqtrade bots, including Hyperopt and FreqAI capabilities.
- **Status:** Initial implementation complete.
- **Details:**
  - [x] Created `15_freqtrade_mcp/` directory with `Dockerfile`, `requirements.txt`, and `mcp_server.py`.
  - [x] Implemented core MCP server structure in `15_freqtrade_mcp/mcp_server.py`:
    - [x] Standard FastMCP setup with Uvicorn and JSON logging.
    - [x] `call_freqtrade_api` helper for Freqtrade REST API interaction.
    - [x] `/health` endpoint.
  - [x] Populated knowledge base tools:
    - [x] `freqtrade.knowledge.hyperoptBestPractices`
    - [xx] `freqtrade.knowledge.freqAiOverview` (marked as double-x to indicate it's done, but typo in original, fixing)
  - [x] Implemented API-based tools for Freqtrade interaction:
    - [x] Bot status & control (getStatus, startBot, stopBot, pauseBot, stopBuy, reloadConfig, getBotHealth, getVersion, showConfig).
    - [x] Financials (getBalance, getProfitSummary, getDailyStats, getPerformance, getTradesHistory, getTrade).
    - [x] Pair & List Management (getWhitelist, getBlacklist, addToBlacklist, deleteFromBlacklist, getLocks, addLock, deleteLock).
    - [x] Forcing Actions (forceEnter, forceExit).
  - [x] Implemented placeholder CLI-based tools:
    - [x] `freqtrade.cli.runHyperopt` (with common parameters).
    - [x] `freqtrade.cli.freqaiTrain` (placeholder, needs CLI verification).
  - [x] Updated `15_freqtrade_mcp/requirements.txt` with `httpx` and pinned versions.
  - [x] Refined `15_freqtrade_mcp/Dockerfile` (non-root user, CMD, dependencies).
  - [x] Created `15_freqtrade_mcp/user_data/` directory (with `.gitkeep`).
  - [x] Created `15_freqtrade_mcp/config_bot.json` (basic Freqtrade bot config with API enabled).
  - [x] Updated `docker-compose.yml`:
    - [x] Added `freqtrade_bot_15` service (for the actual Freqtrade bot).
    - [x] Added `15_freqtrade_mcp` service (for the MCP server).
    - [x] Configured ports, volumes, environment variables (including `FREQTRADE_API_URL`), secrets (`freqtrade_api_password`), and dependencies.
  - [x] Updated `00_master_mcp/mcp_host.py` to proxy `15_freqtrade_mcp` (added `trading.freqtrade` to `FOCUSED_DEFAULT_SERVERS` and corresponding env var to `docker-compose.yml` for master).
  - [x] Created `tests/15_freqtrade_mcp/test_freqtrade_mcp.py` with a basic health check test.
- **Next Steps:**
  - [ ] Add `httpx` to `00_master_mcp/requirements.txt` (if not already there, due to `MCPServiceClient`). (Actually, this was for `00_master_mcp` for its own client, `15_freqtrade_mcp` already has it).
  - [ ] Create `secrets/freqtrade_api_password.txt` with a strong password.
  - [ ] Thoroughly test all implemented tools against a running `freqtrade_bot_15` instance.
  - [ ] Refine `freqtrade.cli.freqaiTrain` tool based on Freqtrade CLI specifics for triggering training.
  - [ ] Develop more comprehensive tests in `tests/15_freqtrade_mcp/test_freqtrade_mcp.py`.

### Workflow Templates
```python
# Example workflow template
deployment_workflow = {
    "name": "deploy_application",
    "description": "Deploy application to Kubernetes",
    "steps": [
        {"service": "secrets", "tool": "getSecret", "params": {"secret_name": "docker-registry"}},
        {"service": "k8s", "tool": "apply_manifest", "params": {"namespace": "production"}},
        {"service": "linux", "tool": "runCommand", "params": {"command": "curl health-check"}}
    ]
}
```

### State Management
```python
class WorkflowStateManager:
    def save_checkpoint(self, workflow_id: str, step: int, state: dict):
        # Save to persistent storage (SQLite/Redis)
        pass
    
    def restore_from_checkpoint(self, workflow_id: str) -> tuple[int, dict]:
        # Restore workflow state
        pass
```

### Advanced Monitoring
- Distributed tracing with correlation IDs
- Performance metrics per service and tool
- Cost tracking for cloud operations
- Compliance reporting

## Production Deployment Checklist

### Security ✅
- [ ] All secrets properly managed (no plaintext)
- [ ] Approval workflows implemented
- [ ] Rate limiting in place
- [ ] Audit logging comprehensive
- [ ] Network security (TLS, firewall rules)
- [ ] Input validation everywhere
- [ ] Path restrictions enforced

### Reliability ✅
- [ ] Health checks for all services
- [ ] Circuit breakers for service calls
- [ ] Retry logic with exponential backoff
- [ ] Graceful degradation
- [ ] Data backup procedures
- [ ] Disaster recovery plan

### Observability ✅
- [ ] Structured logging (JSON format)
- [ ] Metrics collection (Prometheus)
- [ ] Distributed tracing
- [ ] Alerting rules configured
- [ ] Dashboard creation (Grafana)
- [ ] Log aggregation (Loki)

### Performance ✅
- [ ] Load testing completed
- [ ] Resource limits configured
- [ ] Autoscaling policies
- [ ] Database optimization
- [ ] Caching strategy
- [ ] CDN for static assets

## Testing Strategy

### Unit Tests
```python
# Example unit test structure
class TestLinuxCLIService(unittest.TestCase):
    def setUp(self):
        self.service = EnhancedLinuxCLI(port=8001)
    
    def test_command_validation(self):
        is_safe, category, reason = self.service.security.validate_command("ls -la")
        self.assertTrue(is_safe)
        self.assertEqual(category, "read_only")
    
    def test_dangerous_command_rejection(self):
        is_safe, category, reason = self.service.security.validate_command("rm -rf /")
        self.assertFalse(is_safe)
```

### Integration Tests
```python
class TestWorkflowIntegration(unittest.TestCase):
    async def test_multi_service_workflow(self):
        orchestrator = MCPTestClient("http://localhost:8000")
        
        workflow = {
            "id": "test-workflow",
            "steps": [
                {"service": "linux", "tool": "runCommand", "params": {"command": "uptime"}},
                {"service": "k8s", "tool": "list_pods", "params": {"namespace": "default"}}
            ]
        }
        
        result = await orchestrator.call_tool("execute_workflow", workflow)
        self.assertEqual(result["status"], "completed")
```

### Performance Tests
```python
import asyncio
import time

async def performance_test():
    """Test system under load"""
    tasks = []
    for i in range(100):  # 100 concurrent requests
        task = call_orchestrator_tool("get_system_status")
        tasks.append(task)
    
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    print(f"100 requests completed in {end_time - start_time:.2f} seconds")
    success_rate = sum(1 for r in results if r.get("status") == "success") / len(results)
    print(f"Success rate: {success_rate:.2%}")
```

## Monitoring & Alerting

### Key Metrics to Track
1. **Service Health**: Uptime, response time, error rate
2. **Workflow Success**: Completion rate, failure reasons, duration
3. **Security Events**: Failed approvals, rate limit hits, suspicious activity
4. **Resource Usage**: CPU, memory, disk, network per service
5. **Business Metrics**: Tasks completed, services used, user activity

### Alert Rules (Prometheus)
```yaml
groups:
- name: mcp_system
  rules:
  - alert: ServiceDown
    expr: up{job="mcp_services"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "MCP service {{ $labels.instance }} is down"
  
  - alert: HighErrorRate
    expr: rate(mcp_tool_calls_total{status="error"}[5m]) > 0.1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High error rate in {{ $labels.service }}"
```

## Migration Strategy

### From Current State to Enhanced System

1. **Parallel Deployment**
   - Deploy enhanced services alongside current ones
   - Use feature flags to gradually route traffic
   - Monitor performance and reliability

2. **Service-by-Service Migration**
   - Start with least critical services
   - Migrate during low-usage periods
   - Keep rollback procedures ready

3. **Data Migration**
   - Export existing configurations
   - Import into new state management system
   - Verify data integrity

4. **User Training**
   - Document new workflow capabilities
   - Provide training materials
   - Gradual rollout to user groups

## Success Metrics

### Technical KPIs
- **Availability**: 99.9% uptime for critical services
- **Performance**: <500ms response time for 95% of requests
- **Reliability**: <1% error rate for all operations
- **Security**: Zero security incidents, 100% audit coverage

### Business KPIs  
- **Productivity**: 50% reduction in manual infrastructure tasks
- **Efficiency**: 75% faster deployment workflows
- **Quality**: 90% reduction in configuration errors
- **Compliance**: 100% audit trail coverage

This roadmap provides a structured approach to transforming the current MCP system from a well-designed prototype into a production-ready infrastructure automation platform. The key is to implement incrementally while maintaining system stability and security throughout the process.
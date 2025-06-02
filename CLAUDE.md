# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Building and Running Services

```bash
# Build and start all services
docker-compose up --build -d

# Rebuild specific service
docker-compose build <service_name>

# View logs
docker-compose logs -f <service_name>

# Stop all services
docker-compose down
```

### Running Tests

```bash
# Run all tests
python3 run_tests.py

# Run tests for specific service
python -m unittest discover tests/<service_directory>
```

## Architecture Overview

This is a multi-agent MCP (Model Context Protocol) system where each service runs in its own Docker container on a shared `mcp-network`. The architecture follows a hub-and-spoke pattern:

### Central Orchestrator (00_master_mcp)
- **Port**: 8000
- Acts as the MCP Host that coordinates workflows
- Maintains connections to all downstream MCP servers
- Routes requests to appropriate specialized services
- Manages workflow state and correlation IDs

### Service Organization
Each service follows the pattern `NN_servicename_mcp/` where NN is a numeric prefix:
- Service directory contains: `Dockerfile`, `mcp_server.py`, `requirements.txt`, `entrypoint.sh`
- Services expose MCP tools via HTTP/SSE on designated ports (8000-8016)
- All services connect to the shared `mcp-network` Docker network

### Key Service Categories

1. **Infrastructure Management**:
   - `01_linux_cli_mcp` (8001): Linux command execution, SSH operations
   - `08_k8s_mcp` (8008): Kubernetes cluster management
   - `05_vmware_mcp` (8005): VMware infrastructure control

2. **Cloud Providers**:
   - `03_azure_mcp` (8003): Azure resource management
   - `04_google_cloud_mcp` (8004): GCP resource management

3. **Data & Configuration**:
   - `12_cmdb_mcp` (8012): Configuration Management Database
   - `13_secrets_mcp` (8013): Centralized secrets management

4. **AI & Automation**:
   - `14_aider_mcp` (8014): AI coding assistant
   - `15_freqtrade_mcp` (8015): Trading bot knowledge base
   - `16_ai_models_mcp` (8016): LLM gateway (Gemini, Anthropic)

### Service Communication
- Services communicate via HTTP/SSE over the Docker network
- Tool namespacing pattern: `category.subcategory.action` (e.g., `os.linux.runCommand`)
- JSON-based request/response format following MCP protocol
- Correlation IDs flow from orchestrator through all service calls

### Configuration Management
- Environment variables defined in `docker-compose.yml`
- Secrets mounted as read-only volumes or Docker secrets
- Service ports configurable via `MCP_PORT_*` environment variables
- Monitoring stack (Prometheus, Grafana, Loki) for observability

### Security Considerations
- Services run with minimal required privileges
- Secrets mounted read-only from `./secrets/` directory
- Command execution services require approval for modifications
- Network isolation via Docker bridge network

## Implementation Roadmap & Known Issues

### Critical Missing Implementations

#### 1. Web Services (Priority 1)
**06_web_search_mcp** and **07_web_browsing_mcp** - Only README files exist, no actual implementations

```python
# 06_web_search_mcp/mcp_server.py - Basic implementation needed
from duckduckgo_search import DDGS

@mcp_server.tool("web.search.query")
def search_web(query: str, engine: str = "duckduckgo", max_results: int = 5):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return {"query": query, "results": results}
    except Exception as e:
        return {"error": str(e)}
```

#### 2. Service Health Monitoring (Priority 1)
Add to 00_master_mcp:

```python
@mcp.tool("master.getServiceHealth")
async def check_service_health():
    health_status = {}
    for namespace, url in FOCUSED_DEFAULT_SERVERS.items():
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/health", timeout=5.0)
                health_status[namespace] = "healthy" if response.status_code == 200 else "unhealthy"
        except:
            health_status[namespace] = "unreachable"
    return health_status
```

### Service-Specific Issues

#### 00_master_mcp
- Missing workflow state persistence
- No error handling for downstream service failures  
- Workflow engine lacks recovery mechanisms

#### 01_linux_cli_mcp
- Over-engineered SecurityValidator for simple use case
- Hardcoded approval mechanism (not implemented)
- Complex route injection code needs simplification

#### 12_cmdb_mcp
- ServiceNow integration is placeholder/commented out
- Hard-coded port 5012 instead of 8012 in code
- Missing data validation for CMDB entries

#### 16_ai_models_mcp
- No rate limiting implementation
- Missing conversation context management
- No cost/usage tracking for API calls

### Recommended Enhancements

#### 1. Add Workflow State Persistence
```python
# 00_master_mcp/workflow_state.py
import sqlite3
import pickle

class WorkflowStateManager:
    def __init__(self, db_path="/workspace/data/workflows.db"):
        self.db_path = db_path
        self._init_db()
    
    def save_workflow_state(self, workflow_id: str, state: dict):
        # Persist workflow state for recovery
        pass
    
    def load_workflow_state(self, workflow_id: str) -> dict:
        # Load workflow state for recovery
        pass
```

#### 2. Circuit Breaker Pattern
```python
# Add to 00_master_mcp for resilience
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
```

#### 3. Request Caching
```python
# Add to relevant services for performance
import redis
from functools import wraps

def cache_response(ttl=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            # Implementation with Redis or in-memory cache
        return wrapper
    return decorator
```

#### 4. Enhanced Observability
```python
# Add comprehensive metrics across services
from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter('mcp_requests_total', 'Total requests', ['service', 'tool'])
REQUEST_DURATION = Histogram('mcp_request_duration_seconds', 'Request duration')
SERVICE_HEALTH = Gauge('mcp_service_health', 'Service health status', ['service'])
ERROR_RATE = Counter('mcp_errors_total', 'Total errors', ['service', 'error_type'])
```

#### 5. Configuration Management
```yaml
# config/services.yaml - Create centralized config
services:
  timeouts:
    default: 30
    long_running: 300
  rate_limits:
    ai_models: 10  # requests per minute
    web_search: 60
  retry_policies:
    max_attempts: 3
    backoff_factor: 2
  security:
    max_file_size: 10MB
    allowed_file_types: [".txt", ".json", ".yaml", ".md"]
```

### Development Priorities

1. **Implement missing web services** (06, 07) - Critical for functionality
2. **Add service health monitoring** - Essential for production readiness  
3. **Fix service-specific bugs** (CMDB port, approval mechanisms)
4. **Implement workflow persistence** - Important for complex operations
5. **Add rate limiting and caching** - Performance and reliability
6. **Enhance security** - API validation and authentication
7. **Add comprehensive testing** - Quality assurance
8. **Implement monitoring/alerting** - Operations support

### Testing Strategy
```python
# tests/integration/test_workflows.py
import pytest
from tests.fixtures import mock_services

@pytest.mark.asyncio
async def test_end_to_end_workflow():
    # Test complete workflow execution across services
    pass

@pytest.mark.asyncio  
async def test_service_failure_recovery():
    # Test circuit breaker and retry logic
    pass
```

### Known Configuration Issues
- `12_cmdb_mcp` has incorrect port `5012` instead of `8012` in code
- Missing environment validation in several services
- Secrets management needs standardization across services
- Docker health checks not implemented for all services
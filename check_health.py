#!/usr/bin/env python3
"""
One-time health check for all MCP services
"""
import asyncio
import httpx
from datetime import datetime

# Service configuration
SERVICES = {
    "00_master_mcp": {"port": 8080, "name": "Master Orchestrator"},
    "01_linux_cli_mcp": {"port": 8001, "name": "Linux CLI"},
    "08_k8s_mcp": {"port": 8008, "name": "Kubernetes"},
    "12_cmdb_mcp": {"port": 8012, "name": "CMDB"},
    "13_secrets_mcp": {"port": 8013, "name": "Secrets Manager"},
    "14_aider_mcp": {"port": 8014, "name": "Aider AI Assistant"},
    "15_freqtrade_mcp": {"port": 8015, "name": "Freqtrade Knowledge"},
    "16_ai_models_mcp": {"port": 8016, "name": "AI Models Gateway"},
}

async def check_service_health(service_id: str, config: dict) -> dict:
    """Check health of a single service"""
    url = f"http://localhost:{config['port']}/health"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return {
                    "service": service_id,
                    "name": config["name"],
                    "port": config["port"],
                    "status": "✅ healthy",
                    "response_time": f"{response.elapsed.total_seconds()*1000:.1f}ms"
                }
            else:
                return {
                    "service": service_id,
                    "name": config["name"],
                    "port": config["port"],
                    "status": f"⚠️  unhealthy (HTTP {response.status_code})",
                }
    except httpx.ConnectError:
        return {
            "service": service_id,
            "name": config["name"],
            "port": config["port"],
            "status": "❌ offline",
        }
    except Exception as e:
        return {
            "service": service_id,
            "name": config["name"],
            "port": config["port"],
            "status": f"❌ error: {str(e)}",
        }

async def main():
    """Check all services"""
    print(f"\nMCP Services Health Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    tasks = [check_service_health(service_id, config) for service_id, config in SERVICES.items()]
    results = await asyncio.gather(*tasks)
    
    for result in sorted(results, key=lambda x: x['port']):
        status_line = f"Port {result['port']:<5} | {result['name']:<25} | {result['status']}"
        if 'response_time' in result:
            status_line += f" ({result['response_time']})"
        print(status_line)
    
    print("=" * 70)
    
    healthy = sum(1 for r in results if "healthy" in r['status'])
    total = len(results)
    print(f"Summary: {healthy}/{total} services healthy ({healthy/total*100:.0f}%)\n")

if __name__ == "__main__":
    asyncio.run(main())
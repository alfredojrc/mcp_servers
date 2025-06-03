#!/usr/bin/env python3
"""
Health monitoring dashboard for MCP services
"""
import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any
import json

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

async def check_service_health(service_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
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
                    "status": "healthy",
                    "response_time": response.elapsed.total_seconds(),
                    "details": response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                }
            else:
                return {
                    "service": service_id,
                    "name": config["name"],
                    "port": config["port"],
                    "status": "unhealthy",
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}"
                }
    except httpx.ConnectError:
        return {
            "service": service_id,
            "name": config["name"],
            "port": config["port"],
            "status": "offline",
            "error": "Connection refused"
        }
    except httpx.TimeoutException:
        return {
            "service": service_id,
            "name": config["name"],
            "port": config["port"],
            "status": "timeout",
            "error": "Request timed out"
        }
    except Exception as e:
        return {
            "service": service_id,
            "name": config["name"],
            "port": config["port"],
            "status": "error",
            "error": str(e)
        }

async def monitor_all_services():
    """Monitor all services concurrently"""
    tasks = [check_service_health(service_id, config) for service_id, config in SERVICES.items()]
    results = await asyncio.gather(*tasks)
    return results

def print_dashboard(results):
    """Print a formatted dashboard"""
    print("\n" + "="*80)
    print(f"MCP Services Health Dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print(f"{'Service':<20} {'Name':<25} {'Port':<8} {'Status':<12} {'Response Time':<15}")
    print("-"*80)
    
    healthy_count = 0
    total_count = len(results)
    
    for result in sorted(results, key=lambda x: x['port']):
        service = result['service']
        name = result['name']
        port = result['port']
        status = result['status']
        
        # Color coding for terminal
        if status == "healthy":
            status_display = f"\033[92m{status}\033[0m"  # Green
            healthy_count += 1
        elif status == "offline":
            status_display = f"\033[91m{status}\033[0m"  # Red
        else:
            status_display = f"\033[93m{status}\033[0m"  # Yellow
        
        response_time = ""
        if 'response_time' in result:
            response_time = f"{result['response_time']*1000:.1f}ms"
        
        print(f"{service:<20} {name:<25} {port:<8} {status_display:<21} {response_time:<15}")
        
        if 'error' in result and result['error']:
            print(f"  └─ Error: {result['error']}")
    
    print("-"*80)
    print(f"Summary: {healthy_count}/{total_count} services healthy ({healthy_count/total_count*100:.1f}%)")
    print("="*80)

def save_results(results):
    """Save results to JSON file for historical tracking"""
    timestamp = datetime.now().isoformat()
    data = {
        "timestamp": timestamp,
        "results": results
    }
    
    filename = f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filename

async def main():
    """Main monitoring function"""
    while True:
        results = await monitor_all_services()
        print_dashboard(results)
        
        # Save results every hour
        if datetime.now().minute == 0:
            filename = save_results(results)
            print(f"\nResults saved to: {filename}")
        
        # Wait 30 seconds before next check
        await asyncio.sleep(30)

if __name__ == "__main__":
    print("Starting MCP Health Monitor...")
    print("Press Ctrl+C to stop")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
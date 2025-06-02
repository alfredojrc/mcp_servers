#!/usr/bin/env python3
"""
Test and populate the secrets service with container passwords
"""
import httpx
import json
import asyncio

BASE_URL = "http://localhost:8013"

async def test_secrets_service():
    """Test the secrets service and add some sample secrets"""
    
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        print("Testing health endpoint...")
        response = await client.get(f"{BASE_URL}/health")
        print(f"Health status: {response.json()}")
        
        # Test MCP tools endpoint
        print("\nChecking available MCP tools...")
        response = await client.get(f"{BASE_URL}/tools")
        if response.status_code == 200:
            tools = response.json()
            print(f"Available tools: {json.dumps(tools, indent=2)}")
        
        # List of container passwords to add
        container_secrets = [
            # MCP Services
            ("mcp_master_password", "secure_master_pass_2025"),
            ("mcp_cmdb_password", "cmdb_secure_pass_2025"),
            ("mcp_linux_cli_ssh_key", "ssh-rsa AAAAB3NzaC1yc2EAAAAD..."),
            
            # Database passwords
            ("postgres_password", "postgres_secure_2025"),
            ("redis_password", "redis_secure_2025"),
            ("mysql_root_password", "mysql_root_2025"),
            
            # API Keys
            ("anthropic_api_key", "sk-ant-..."),  # Placeholder
            ("gemini_api_key", "AIza..."),        # Placeholder
            ("openai_api_key", "sk-..."),         # Placeholder
            
            # Trading Platform Credentials
            ("freqtrade_api_user", "freqtrader"),
            ("freqtrade_api_password", "freqtrade_secure_2025"),
            ("hawkeye_admin_password", "hawkeye_admin_2025"),
            ("geminifreq_admin_password", "geminifreq_admin_2025"),
            ("claudefreq_admin_password", "claudefreq_admin_2025"),
            
            # Monitoring Credentials
            ("grafana_admin_password", "grafana_admin_2025"),
            ("prometheus_admin_password", "prom_admin_2025"),
            ("kibana_admin_password", "kibana_admin_2025"),
            
            # Exchange API Keys (placeholders)
            ("binance_api_key", "binance_key_placeholder"),
            ("binance_api_secret", "binance_secret_placeholder"),
            ("kraken_api_key", "kraken_key_placeholder"),
            ("kraken_api_secret", "kraken_secret_placeholder"),
        ]
        
        print("\nTesting secret retrieval with environment variable backend...")
        # Since we're using environment variables, we need to set them first
        # or use the KeePass backend if available
        
        # Try to get a secret (this will likely fail without proper backend setup)
        test_key = "test_secret"
        print(f"\nTrying to retrieve secret: {test_key}")
        
        try:
            # Construct MCP request
            mcp_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "secrets.get",
                    "arguments": {
                        "key": test_key
                    }
                },
                "id": 1
            }
            
            response = await client.post(
                f"{BASE_URL}/call",
                json=mcp_request,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Response: {response.json()}")
            
        except Exception as e:
            print(f"Error retrieving secret: {e}")
        
        print("\nNote: To properly use the secrets service, you need to:")
        print("1. Set up a KeePass database with the passwords")
        print("2. Or configure environment variables for each secret")
        print("3. Or set up Azure Key Vault / Google Secret Manager")

if __name__ == "__main__":
    asyncio.run(test_secrets_service())
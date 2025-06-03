#!/usr/bin/env python3
"""
Configure secrets for MCP services using environment variables
"""
import os
import sys
from pathlib import Path

def create_env_file():
    """Create a .env file template for secrets"""
    env_template = """# MCP Services Secrets Configuration
# Copy this to .env and fill in your actual values

# API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Database Passwords
POSTGRES_PASSWORD=secure_postgres_password
REDIS_PASSWORD=secure_redis_password
MYSQL_ROOT_PASSWORD=secure_mysql_password

# Service Passwords
CMDB_ADMIN_PASSWORD=secure_cmdb_password
SECRETS_ADMIN_PASSWORD=secure_secrets_password
FREQTRADE_API_PASSWORD=secure_freqtrade_password

# KeePass Master Password
KEEPASS_MASTER_PASSWORD=secure_keepass_master_password

# Exchange API Keys (if needed)
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret

# Cloud Provider Credentials
AZURE_CLIENT_ID=your_azure_client_id
AZURE_CLIENT_SECRET=your_azure_client_secret
AZURE_TENANT_ID=your_azure_tenant_id

GCP_PROJECT_ID=your_gcp_project_id
# GCP credentials are typically provided via service account JSON file

# ServiceNow Integration
SERVICENOW_INSTANCE=your_instance_name
SERVICENOW_USER=api_user
SERVICENOW_PASSWORD=secure_servicenow_password
"""
    
    env_file = Path(".env.example")
    env_file.write_text(env_template)
    print(f"Created {env_file}")
    
    # Create actual .env if it doesn't exist
    actual_env = Path(".env")
    if not actual_env.exists():
        actual_env.write_text(env_template)
        print(f"Created {actual_env} - Please update with your actual values!")
    else:
        print(f"{actual_env} already exists")

def create_docker_secrets():
    """Create Docker secrets files"""
    secrets_dir = Path("secrets")
    
    # Ensure secrets directory has proper permissions
    os.chmod(secrets_dir, 0o700)
    
    # Create placeholder files for required secrets
    secret_files = {
        "anthropic_api_key.txt": "# Add your Anthropic API key here",
        "gemini_api_key.txt": "# Add your Gemini API key here",
        "keepass_master_password.txt": "# Add your KeePass master password here",
        "freqtrade_api_password.txt": "# Add your Freqtrade API password here",
    }
    
    for filename, placeholder in secret_files.items():
        filepath = secrets_dir / filename
        if not filepath.exists():
            filepath.write_text(placeholder)
            os.chmod(filepath, 0o600)  # Read/write for owner only
            print(f"Created {filepath}")
        else:
            print(f"{filepath} already exists")

def setup_keepass_env():
    """Set up environment variables for KeePass"""
    keepass_vars = {
        "KEEPASS_DB_PATH": "/secrets/keepass/mcp_secrets.kdbx",
        "KEEPASS_PASSWORD_SECRET_PATH": "/run/secrets/keepass_master_password",
    }
    
    print("\nKeePass environment variables to set:")
    for key, value in keepass_vars.items():
        print(f"export {key}={value}")

def create_secrets_readme():
    """Create a README for secrets management"""
    readme_content = """# Secrets Management for MCP Services

## Overview
This directory contains secrets and sensitive configuration for MCP services.

## Security Best Practices

1. **Never commit secrets to version control**
   - Add all secret files to .gitignore
   - Use environment variables or Docker secrets

2. **File Permissions**
   - Secrets directory: 700 (owner only)
   - Secret files: 600 (owner read/write only)

3. **Docker Secrets**
   - Secrets are mounted as read-only volumes
   - Available at /run/secrets/<secret_name> inside containers

4. **Environment Variables**
   - Use .env file for local development
   - Use Docker secrets for production

## Setting Up Secrets

1. Copy .env.example to .env and fill in your values
2. Create individual secret files in the secrets/ directory
3. Ensure proper file permissions (chmod 600)
4. Never share or expose these files

## KeePass Integration

The secrets service can use KeePass for centralized password management:
- Database: secrets/keepass/mcp_secrets.kdbx
- Master password: stored in secrets/keepass_master_password.txt

## Service-Specific Secrets

### API Keys
- anthropic_api_key.txt - For AI Models MCP
- gemini_api_key.txt - For AI Models MCP
- openai_api_key.txt - For Aider MCP

### Databases
- postgres_password.txt - PostgreSQL databases
- redis_password.txt - Redis instances

### Services
- freqtrade_api_password.txt - Freqtrade bot API
- servicenow_password.txt - ServiceNow integration

## Troubleshooting

If services can't access secrets:
1. Check file permissions
2. Verify Docker volume mounts
3. Check container logs for permission errors
4. Ensure secret files exist and aren't empty
"""
    
    readme_path = Path("secrets/README.md")
    readme_path.write_text(readme_content)
    print(f"\nCreated {readme_path}")

def main():
    """Main setup function"""
    print("Setting up secrets configuration for MCP services...")
    
    # Create necessary directories
    Path("secrets").mkdir(exist_ok=True)
    Path("secrets/keepass").mkdir(exist_ok=True)
    
    # Set up configurations
    create_env_file()
    create_docker_secrets()
    setup_keepass_env()
    create_secrets_readme()
    
    print("\n✅ Secrets configuration complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your actual values")
    print("2. Update secret files in secrets/ directory")
    print("3. Set proper permissions: chmod 600 secrets/*")
    print("4. Restart services to apply new secrets")

if __name__ == "__main__":
    main()
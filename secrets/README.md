# Secrets Management for MCP Services

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
